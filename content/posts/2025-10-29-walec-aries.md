---
title: "Walec ARIES – jak SQL zapisuje historię transakcji"
date: 2025-10-29
slug: walec-aries
tags: [SQLServer, Internals, WAL, ARIES, Recovery]
draft: false
---

SQL Server nie zapomina.  
Zanim zapisze dane na dysk, zapisuje **historię tego, co ma się wydarzyć**.  
To właśnie mechanizm **ARIES (Algorithm for Recovery and Isolation Exploiting Semantics)** – serce niezawodności systemu transakcyjnego.

> „Historia to pamięć systemu.” — SQLManiak

---

## ⚙️ Write-Ahead Logging (WAL)

Każda modyfikacja w SQL Serverze przechodzi przez log transakcyjny (`.ldf`):
1. Tworzy wpis logu z informacją o zmianie (LSN – Log Sequence Number),
2. Wpis trafia na dysk (flush logu),
3. Dopiero wtedy zmieniona strona danych może zostać zapisana.

To zasada **Write-Ahead Logging (WAL)** – najpierw log, potem dane.  
Dzięki niej SQL Server wie, *co się wydarzyło nawet po awarii*.

---

## 🔁 ARIES w trzech aktach

Kiedy serwer uruchamia się po awarii, nie zgaduje. On **czyta log** i rekonstruuje świat.

| Faza | Co się dzieje | Cel |
|------|----------------|-----|
| **Analysis** | Identyfikuje aktywne transakcje i zmodyfikowane strony | „Kto był w trakcie pracy?” |
| **Redo** | Powtarza wszystkie operacje zatwierdzone | „Odtwarzamy rzeczywistość.” |
| **Undo** | Wycofuje niezatwierdzone transakcje | „Porządkujemy chaos.” |

> ARIES to jak odtwarzanie filmu: przewijasz taśmę do checkpointu, potem do przodu i usuwasz ostatnie klatki, których nie zatwierdzono.

---

## 🧩 Jak wygląda wpis logu?

Każda zmiana generuje wpis z polami:

| Pole | Znaczenie |
|------|------------|
| **LSN** | numer sekwencyjny wpisu |
| **PrevLSN** | poprzedni wpis tej transakcji |
| **Transaction ID** | unikalny identyfikator transakcji |
| **PageID / FileID** | identyfikacja strony danych |
| **Operation** | np. `LOP_INSERT_ROWS`, `LOP_COMMIT_XACT` |
| **Before/After Image** | wartości przed i po zmianie |

Sekwencja tych wpisów to „czarna skrzynka” SQL Servera.

---

## 🔍 Zajrzyj w DMV i log

```sql
-- aktywność logu dla bieżącej bazy
SELECT name, log_reuse_wait_desc, recovery_model_desc
FROM sys.databases
WHERE database_id = DB_ID();
```

```sql
-- podgląd użycia logu
DBCC SQLPERF(LOGSPACE);
```

```sql
-- odczyt surowego logu (tylko lab!)
SELECT [Current LSN], [Operation], [Transaction ID], [Transaction Name], [Context]
FROM fn_dblog(NULL, NULL)
WHERE [Transaction Name] IS NOT NULL;
```

---

## 🧪 Mini-demo – ARIES w akcji

```sql
USE tempdb;
GO
CREATE TABLE dbo.LogDemo(id INT IDENTITY, txt NVARCHAR(100));
GO
BEGIN TRAN
INSERT INTO dbo.LogDemo VALUES (N'Pierwszy wpis');
INSERT INTO dbo.LogDemo VALUES (N'Drugi wpis');
ROLLBACK TRAN;
```

W logu zobaczysz wpisy:
`LOP_BEGIN_XACT → LOP_INSERT_ROWS → LOP_ABORT_XACT`

Każdy z nich ma własny **LSN**, a SQL Server wie dokładnie,
które zmiany trzeba cofnąć podczas fazy *Undo*.

---

## ⚡ Checkpoint i Recovery

Checkpoint to punkt kontrolny – SQL Server zapisuje wszystkie strony na dysk
i notuje w logu, że do tego miejsca baza jest spójna.

Po restarcie:
1. Szuka checkpointu (`last_checkpoint_lsn`),
2. Uruchamia **Analysis**, **Redo**, **Undo**,
3. Przywraca bazę do stanu sprzed awarii.

Zajrzyj do DMV:

```sql
SELECT database_id, last_checkpoint_lsn FROM sys.database_recovery_status;
```

---

## 🧠 Monitorowanie logu

```sql
-- użycie logu (rozmiar, procent)
SELECT total_log_size_in_bytes/1024/1024 AS TotalMB,
       used_log_space_in_bytes/1024/1024 AS UsedMB,
       used_log_space_in_percent AS UsedPercent
FROM sys.dm_db_log_space_usage;

-- aktywne transakcje
SELECT transaction_id, name, transaction_begin_time, transaction_state
FROM sys.dm_tran_active_transactions;
```

---

## ⚙️ Dobre praktyki

✅ **Regularny BACKUP LOG** w modelu FULL  
✅ **Krótko trwające transakcje** – log nie zwalnia się, dopóki są aktywne  
✅ **Szybki dysk dla `.ldf`** – log to najczęściej zapisywany plik  
✅ **Monitoruj `log_reuse_wait_desc`** – jeśli długo stoi na `ACTIVE_TRANSACTION`, coś blokuje odzysk miejsca  
✅ **Nie usuwaj ręcznie logu!**  

---

## 🧩 Zrozumienie ARIES to zrozumienie SQL Servera

ARIES to nie magiczny skrót z podręcznika – to mechanizm, który codziennie ratuje Twoje dane.  
To on wie, jak **cofnąć czas**, jak **zrekonstruować** świat po awarii i jak **utrzymać spójność** mimo chaosu transakcji.

> „SQL Server nie zapomina. On pamięta – w logu.” — SQLManiak

---

📘 Repozytorium z demem:  
👉 [ARIES](https://github.com/marcinpytlik/SQLManiak/blob/master/sqlmaniak_blog/ARIES/README.md)
