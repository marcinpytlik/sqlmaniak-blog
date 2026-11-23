---
title: "Die ARIES-Engine: Wie SQL Server Transaktionshistorie speichert"
date: 2025-10-29
slug: walec-aries
tags: [SQLServer, Internals, WAL, ARIES, Recovery]
draft: false
---

SQL Server vergisst nicht. Bevor geänderte Datenseiten auf den Datenträger geschrieben werden, erfasst die Engine **die Historie der Änderungen**. Das ist die Grundlage von **ARIES (Algorithm for Recovery and Isolation Exploiting Semantics)**, einem wichtigen Bestandteil zuverlässiger Transaktionsverarbeitung.

> „Geschichte ist das Gedächtnis eines Systems.“ — SQLManiak

---

## ⚙️ Write-Ahead Logging (WAL)

Jede Änderung in SQL Server wird im Transaktionsprotokoll (`.ldf`) erfasst:

1. Ein Protokolleintrag beschreibt die Änderung und erhält eine LSN (Log Sequence Number).
2. Der Eintrag wird dauerhaft auf den Datenträger geschrieben.
3. Erst danach darf die geänderte Datenseite auf den Datenträger geschrieben werden.

Das ist **Write-Ahead Logging (WAL)**: zuerst das Log, dann die Datenseite. So kann SQL Server nach einem Ausfall wiederhergestellt werden.

---

## 🔁 ARIES in drei Akten

Nach einem Absturz muss der Server nicht raten. Er **liest das Log** und rekonstruiert den Datenbankzustand.

| Phase | Was passiert? | Ziel |
|---|---|---|
| **Analysis** | Erkennt aktive Transaktionen und Dirty Pages | „Wer war noch beschäftigt?“ |
| **Redo** | Wiederholt notwendige protokollierte Änderungen | „Den Zustand rekonstruieren.“ |
| **Undo** | Macht nicht abgeschlossene Transaktionen rückgängig | „Unerledigte Arbeit bereinigen.“ |

> ARIES ähnelt der Wiedergabe eines Films: Einen geeigneten Wiederherstellungspunkt finden, erforderliche Änderungen wiederholen und unvollendete Aktionen zurücknehmen.

---

## 🧩 Was enthält ein Logeintrag?

Ein Logeintrag kann Felder wie diese enthalten:

| Feld | Bedeutung |
|---|---|
| **LSN** | Fortlaufende Kennung des Logeintrags |
| **PrevLSN** | Vorheriger Eintrag derselben Transaktion |
| **Transaction ID** | Eindeutige Transaktionskennung |
| **PageID / FileID** | Kennung der Datenseite |
| **Operation** | Zum Beispiel `LOP_INSERT_ROWS` oder `LOP_COMMIT_XACT` |
| **Before/After Image** | Je nach Operation Informationen über die Änderung |

Die Folge dieser Einträge ist die Blackbox von SQL Server.

---

## 🔍 DMVs und Log untersuchen

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

## 🧪 Mini-Demo: ARIES in Aktion

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

Im Log findest du Einträge wie:
`LOP_BEGIN_XACT → LOP_INSERT_ROWS → LOP_ABORT_XACT`

Jeder besitzt eine eigene **LSN**, sodass SQL Server bestimmen kann, welche Änderungen rückgängig gemacht werden müssen.

---

## ⚡ Checkpoint und Recovery

Ein Checkpoint begrenzt die Wiederherstellungsarbeit, indem er Dirty Pages schreibt und Recovery-Informationen erfasst. Das bedeutet nicht, dass alle Transaktionen committed wurden oder keine Recovery mehr erforderlich ist.

Nach einem Neustart verwendet SQL Server Metadaten und Logeinträge für **Analysis**, **Redo** und **Undo**, um einen transaktional konsistenten Zustand wiederherzustellen.

Ein Blick in die DMV:

```sql
SELECT database_id, last_checkpoint_lsn FROM sys.database_recovery_status;
```

---

## 🧠 Das Log überwachen

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

## ⚙️ Bewährte Vorgehensweisen

✅ **Regelmäßige Transaktionslog-Backups** im FULL-Modell.  
✅ **Kurze Transaktionen**, damit die Wiederverwendung des Logs nicht lange blockiert wird.  
✅ **Schneller Speicher für die `.ldf`-Datei**, in die häufig geschrieben wird.  
✅ **`log_reuse_wait_desc` überwachen** — ein dauerhaftes `ACTIVE_TRANSACTION` kann auf eine offene Transaktion hinweisen.  
✅ **Das Transaktionslog niemals manuell löschen.**

---

## 🧩 ARIES verstehen heißt SQL Server verstehen

ARIES ist nicht nur eine Abkürzung im Lehrbuch. Es ist ein Recovery-Mechanismus, der täglich Daten schützt. Er kann **unvollständige Arbeit zurücknehmen**, Änderungen nach einem Ausfall **rekonstruieren** und trotz Transaktionschaos **Konsistenz bewahren**.

> „SQL Server vergisst nicht. Er erinnert sich — im Log.“ — SQLManiak

---

📘 Demo-Repository:
👉 [ARIES](https://github.com/marcinpytlik/SQLManiak/blob/master/sqlmaniak_blog/ARIES/README.md)
