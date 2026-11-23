---
title: "Ghost Cleanup Task in Aktion"
date: 2025-10-23
slug: ghost-cleanup-task
tags: [SQLServer, Internals, GhostRecords, DMV, Performance]
draft: false
---

SQL Server ähnelt einem Organismus, der sich selbst sauber halten kann. Wird eine Zeile gelöscht, verschwindet ihr Geist nicht sofort — er bleibt in der Datenstruktur zurück, wie die Spur einer abgestorbenen Zelle. Erst der *Ghost Cleanup Task* räumt später still auf und stellt das Gleichgewicht wieder her.

Er ist das Immunsystem von SQL Server: Er arbeitet unbemerkt im Hintergrund und verhindert, dass die Datenbank mit toten Datensätzen überfüllt wird.

---

## 🔍 Ein Blick in die DMV

```sql
-- znajdź indeksy zawierające ghost records
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED')
WHERE ghost_record_count > 0;
```

> „Ordnung ist nicht die Abwesenheit von Chaos, sondern die Fähigkeit, es zu beherrschen.“ — Kant zugeschrieben

---

## 🧪 Lab: Geister in Aktion beobachten

Dieses Experiment zeigt, dass ein gelöschter Datensatz physisch nicht unbedingt sofort verschwindet.

### 1️⃣ Testumgebung erstellen

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

### 2️⃣ Einen Teil der Daten löschen

```sql
DELETE TOP (5000) FROM dbo.GhostDemo;
GO
```

### 3️⃣ Indexstruktur untersuchen

```sql
-- jeszcze przed sprzątaniem
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.GhostDemo'), NULL, NULL, 'DETAILED');
```

### 4️⃣ Ghost Cleanup Task anstoßen

Normalerweise läuft die Bereinigung asynchron, du kannst sie aber ausdrücklich anfordern:

```sql
-- uruchom wewnętrzny task
DBCC FORCEGHOSTCLEANUP;
GO
```

### 5️⃣ Erneut prüfen

```sql
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.GhostDemo'), NULL, NULL, 'DETAILED');
```

📊 Nach einer Weile kann `ghost_record_count` sinken, wenn die Ghost Records bereinigt wurden.

---

## 🔬 Internals

Ghost Cleanup läuft als eigenständiger **Hintergrundtask** innerhalb von SQL Server. Er untersucht regelmäßig Seiten mit Ghost Records und entfernt geeignete Datensätze verzögert, um parallele Workloads möglichst wenig zu beeinträchtigen.

Wichtige Fakten:
- er arbeitet **instanzweit**, nicht als eigener Task für jede Datenbank,
- das Intervall liegt **ungefähr bei 10 Sekunden**, abhängig von Version und Aktivität,
- die Bereinigung nutzt **kooperatives Scheduling**,
- sie kann mit `DBCC FORCEGHOSTCLEANUP` angefordert werden,
- Tabellen in **In-Memory OLTP** besitzen eigene Garbage-Collection-Mechanismen.

---

## 🧠 Das solltest du dir merken

| Begriff | Beschreibung |
|---|---|
| Ghost Record | Ein als gelöscht markierter Datensatz, der physisch noch auf einer Datenseite liegt. |
| Cleanup Task | Ein Hintergrundprozess, der geeignete Ghost Records asynchron entfernt. |
| DMV | `sys.dm_db_index_physical_stats` zeigt die Anzahl der Ghost Records. |
| Explizite Anforderung | `DBCC FORCEGHOSTCLEANUP` fordert die Bereinigung an. |

---

> 💡 **Profi-Tipp:** Wenn Datendateien wachsen oder die Fragmentierung hoch ist, prüfe, ob umfangreiche DELETE-Operationen viele Ghost Records hinterlassen haben. Manchmal kann ein *ALTER INDEX REBUILD* sinnvoll sein.

---
