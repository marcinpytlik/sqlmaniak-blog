---
title: "Ghost Cleanup Task w akcji"
date: 2025-10-23
slug: ghost-cleanup-task
tags: [SQLServer, Internals, GhostRecords, DMV, Performance]
draft: false
---

SQL Server przypomina organizm, który potrafi sam utrzymać czystość.  
Gdy rekord zostaje usunięty, jego duch nie znika od razu — pozostaje w strukturze danych, jak ślad po zmarłej komórce.  
Dopiero *Ghost Cleanup Task* przychodzi, by po cichu posprzątać, przywracając równowagę systemu.

To układ odpornościowy SQL Servera – działa w tle, gdy nikt nie patrzy, i dba o to, by baza nie zarosła martwymi danymi.

---

## 🔍 Zajrzyj w DMV

```sql
-- znajdź indeksy zawierające ghost records
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED')
WHERE ghost_record_count > 0;
```
> „Porządek nie polega na braku chaosu, lecz na jego kontrolowaniu.” — Kant

---

## 🧪 Lab: Zobacz duchy w akcji

Poniższy eksperyment pokazuje, że usunięty rekord nie znika natychmiast.

### 1️⃣ Utwórz środowisko testowe

```sql
USE tempdb;
GO
IF OBJECT_ID('dbo.GhostDemo') IS NOT NULL DROP TABLE dbo.GhostDemo;
CREATE TABLE dbo.GhostDemo
(
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Payload CHAR(100) NOT NULL DEFAULT REPLICATE('x', 100)
);
GO

INSERT INTO dbo.GhostDemo DEFAULT VALUES;
GO 10000
```

### 2️⃣ Usuń część danych

```sql
DELETE TOP (5000) FROM dbo.GhostDemo;
GO
```

### 3️⃣ Zajrzyj w strukturę indeksu

```sql
-- jeszcze przed sprzątaniem
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.GhostDemo'), NULL, NULL, 'DETAILED');
```

### 4️⃣ Wymuś aktywację Ghost Cleanup Task

Normalnie działa asynchronicznie, ale możesz go przyspieszyć:

```sql
-- uruchom wewnętrzny task
DBCC FORCEGHOSTCLEANUP;
GO
```

### 5️⃣ Zweryfikuj ponownie

```sql
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.GhostDemo'), NULL, NULL, 'DETAILED');
```
📊 Po chwili zobaczysz, że `ghost_record_count` spada — duchy zostały uprzątnięte.

---

## 🔬 Internals

Ghost Cleanup działa jako osobny *background task* w ramach **Resource Monitor Scheduler**.  
Zadanie to regularnie przeszukuje stronice oznaczone flagą *GHOST*, a następnie usuwa rekordy w trybie odroczonym, aby zminimalizować blokady.

Najważniejsze fakty:
- działa **globalnie na instancji**, nie per baza,
- interwał działania to **około 10 sekund** (może się różnić w zależności od aktywności),
- cleanup odbywa się w **trybie cooperative scheduling**,
- można go wymusić przez `DBCC FORCEGHOSTCLEANUP`,
- nie dotyczy tabel w **In-Memory OLTP**, które mają własne mechanizmy GC.

---

## 🧠 Warto zapamiętać

| Zjawisko | Opis |
|-----------|------|
| Ghost Record | Rekord oznaczony jako usunięty, ale fizycznie wciąż na stronie danych. |
| Cleanup Task | Proces asynchroniczny, który usuwa duchy w tle. |
| DMV | `sys.dm_db_index_physical_stats` pokazuje liczbę ghost records. |
| Wymuszenie | `DBCC FORCEGHOSTCLEANUP` uruchamia czyszczenie natychmiast. |

---

> 💡 **Pro Tip:** Jeśli masz problem z rozrostem plików danych lub fragmentacją, sprawdź, czy nie masz nadmiaru ghost records po masowych DELETE — czasem warto wykonać *ALTER INDEX REBUILD*.

---

