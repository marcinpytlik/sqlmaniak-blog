---
title: "PAGE Restore – chirurgia bazy danych"
date: 2025-10-24
slug: page-restore
tags: [SQLServer, Backup, Restore, Internals, PageRestore]
draft: false
---

Kiedy baza ma miliardy stron danych, pełny restore bywa jak przeszczep serca.  
Ale czasem wystarczy precyzyjna operacja – przywrócenie tylko uszkodzonej strony.  
*PAGE restore* to chirurgiczna procedura SQL Servera: przywraca fragment, nie zatrzymując całego organizmu.

## 🧩 Idea

Każdy obiekt w SQL Server składa się z 8-KB stron.  
Gdy jedna z nich zostanie uszkodzona (błąd I/O, dysk, checksum), silnik **oznacza ją jako suspect** i pozwala na przywrócenie *tylko tej strony* z backupu — bez pełnego przywracania całej bazy czy pliku danych.

To jeden z najbardziej precyzyjnych mechanizmów **Database Engine Recovery Infrastructure**.

## 🧠 Kiedy można wykonać PAGE RESTORE

✅ Baza musi być w trybie **FULL** lub **BULK_LOGGED**.  
✅ Musisz mieć:
- **Full backup** (lub differential, jeśli istnieje),
- **Transaction log backup** (aby odtworzyć zmiany po pełnym),
- Identyfikatory uszkodzonych stron (`file_id:page_id`).

## 🔍 Diagnoza

```sql
-- sprawdź, które strony zostały oznaczone jako uszkodzone
SELECT database_id, file_id, page_id, event_type, error_count, last_update_date
FROM msdb.dbo.suspect_pages;
```

Wartość `event_type`:
- `1` – 823 error (I/O),
- `2` – bad checksum,
- `3` – torn page,
- `4` – restored,
- `5` – deallocated,
- `7` – bad header.

## 🧪 Demo (laboratoryjne)

```sql
-- 1️⃣ Wymuszenie błędu (symulacja – nie rób w produkcji!)
DBCC WRITEPAGE ('AdventureWorks2022', 1, 200, 0, 1, 0x45, 1);

-- 2️⃣ Próba odczytu
DBCC CHECKDB('AdventureWorks2022') WITH NO_INFOMSGS, ALL_ERRORMSGS;
GO
SELECT * FROM msdb.dbo.suspect_pages;

-- 3️⃣ PAGE RESTORE – przywracamy tylko uszkodzoną stronę (1:200)
RESTORE DATABASE AdventureWorks2022
PAGE='1:200'
FROM DISK = 'D:\Backups\AdventureWorks2022_FULL.bak'
WITH NORECOVERY;
GO

-- 4️⃣ Odtwarzamy logi, by baza była spójna
RESTORE LOG AdventureWorks2022
FROM DISK = 'D:\Backups\AdventureWorks2022_LOG.trn'
WITH RECOVERY;
GO
```

> Efekt: tylko jedna 8-KB strona została przywrócona,  
> baza wróciła do spójnego stanu — bez zatrzymywania całości.

## 📊 DMV po operacji

```sql
SELECT * FROM msdb.dbo.suspect_pages WHERE event_type = 4;
```

Jeżeli pojawi się `event_type = 4`, oznacza to, że strona została skutecznie odtworzona.

## 🧰 Przydatne narzędzia diagnostyczne

| Narzędzie | Cel |
|------------|-----|
| `DBCC CHECKDB` | wykrycie i raport uszkodzeń |
| `msdb.dbo.suspect_pages` | rejestr błędów stron |
| `DBCC PAGE` | odczyt zawartości konkretnej strony (tylko dla laboratoriów) |
| `RESTORE HEADERONLY / FILELISTONLY` | sprawdzenie backupów przed operacją |
| `sys.dm_io_virtual_file_stats` | I/O metryki dla potwierdzenia naprawy |

## 🧩 Strategia DBA

PAGE RESTORE to narzędzie ratunkowe — nie zastępuje pełnych backupów.  
Warto je mieć w planie DR jako **operację punktową**, np.:
- przy uszkodzeniu pojedynczego obiektu w dużej bazie (>1 TB),
- gdy nie można zatrzymać instancji,
- lub gdy dane są replikowane i trzeba ograniczyć downtime.

> „Sztuka naprawy polega na zrozumieniu, które fragmenty należy zostawić w spokoju.”  
> — *inspiracja: William James*

📚 **Do repo:**  
[SQLManiak/docs/PageRestore](https://github.com/marcinpytlik/SQLManiak/tree/master/docs/PageRestore.sql)

### 🧩 Checklista:
- [ ] Tryb FULL / BULK_LOGGED  
- [ ] Zidentyfikowane `file_id:page_id`  
- [ ] Dostępny pełny i log backup  
- [ ] Test `RESTORE VERIFYONLY`  
- [ ] `RESTORE DATABASE … PAGE = 'X:Y' WITH NORECOVERY`  
- [ ] `RESTORE LOG … WITH RECOVERY`  
- [ ] Weryfikacja: `DBCC CHECKDB` + `suspect_pages`  

*PAGE restore – chirurgia, nie transplantacja.  
Nie naprawiasz wszystkiego, tylko to, co wymaga dotyku.*
