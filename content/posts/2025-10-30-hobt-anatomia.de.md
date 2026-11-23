---
title: "HOBT: Die Hierarchie der Datenorganisation"
date: 2025-10-30
slug: hobt-anatomia
tags: [SQLServer, Internals, Indexes, HOBT, Storage]
draft: false
---

Daten liegen in SQL Server nicht ungeordnet herum. Sie bilden Strukturen, deren Zweige zu Datenseiten führen. **HOBT (Heap Or B-Tree)** ist die Speicherstruktur hinter jedem B-Tree-Index und jeder Heap-Tabelle. Es ist das Gerüst der Datenorganisation und Adressierung — von der *Wurzel* über Zwischenebenen bis zu den *Blattseiten* eines B-Trees.

> „Struktur ist die Form, in der Ordnung existiert.“ — SQLManiak

---

## 🧩 Was ist ein HOBT in der Praxis?

Jede Partition eines Index oder Heaps besitzt **ein HOBT** (eine Tabelle mit einer Partition und drei Indizes hat vier HOBTs; eine Tabelle mit vier Partitionen und zwei Indizes hat acht).

**HOBT ist nicht mit einem Indexobjekt gleichzusetzen**: Es beschreibt die physische Struktur einer bestimmten Index- oder Heap-Partition.

🆔 **HOBT-Kennung:** `hobt_id` — während der Lebensdauer der Struktur zugeordnet, kann sich aber nach bestimmten Rebuild-Operationen ändern.

---

## 📦 HOBTs und Allocation Units

Eine zu einem HOBT gehörende Partition kann bis zu **drei Typen von Allocation Units** verwenden:

- **IN_ROW_DATA** — Zeilen auf regulären 8-KB-Datenseiten.
- **ROW_OVERFLOW_DATA** — variable Daten, die wegen der Zeilenlänge außerhalb der eigentlichen Zeile gespeichert werden.
- **LOB_DATA** — große Objekte wie XML und `VARBINARY(MAX)`.

📎 Beziehung:
`sys.allocation_units.container_id = sys.partitions.hobt_id` für IN_ROW_DATA und ROW_OVERFLOW_DATA; LOB_DATA verwendet stattdessen die Partitionskennung.

---

## 🌲 Heaps und B-Trees im Vergleich

**Heap:**
- kein Clustered-Index-Schlüssel,
- Datenseiten sind **nicht logisch nach einem Clustered Key sortiert**,
- Updates, die Zeilen vergrößern, können *Forwarded Records* erzeugen.

**B-Tree-Index:**
- geordnete Indexstruktur,
- die Blattebene eines Clustered Index enthält die Datenzeilen der Tabelle,
- die Blattebene eines Nonclustered Index enthält Schlüssel und Zeilenverweise (`RID` oder Clustered Key).

---

## 🗺️ Seitenkarten und Metadaten

**Metadaten und Zuordnungskarten:** `PFS` (Page Free Space), `GAM`/`SGAM` (Extent-Zuordnung) und `IAM` (Index Allocation Map) verbinden Speicherstrukturen mit zugeordneten Seiten.

**Baumdiagnose:**
- `sys.dm_db_index_physical_stats` — Ebenen, Fragmentierung, Forwarded Records,
- `sys.dm_db_database_page_allocations` — Zuordnungsdetails (undokumentiert),
- `DBCC PAGE/IND` — tiefere Analyse (undokumentiert).

---

## 🔍 Schnelle DMVs: HOBTs in deiner Datenbank

### 📘 HOBT-Übersicht

```sql
SELECT
  o.name              AS ObjectName,
  i.name              AS IndexName,
  i.index_id,
  p.partition_number,
  p.hobt_id,
  au.type_desc        AS AU_Type,
  au.total_pages,
  au.used_pages
FROM sys.partitions AS p
JOIN sys.objects   AS o  ON o.object_id = p.object_id
LEFT JOIN sys.indexes   AS i  ON i.object_id = p.object_id AND i.index_id = p.index_id
LEFT JOIN sys.allocation_units AS au ON au.container_id = p.hobt_id
WHERE o.type = 'U'
ORDER BY ObjectName, IndexName, partition_number, AU_Type;
```

---

### 📊 Baumebenen und physische Statistiken

```sql
SELECT
  OBJECT_NAME(ips.object_id) AS ObjectName,
  ips.index_id,
  ips.index_type_desc,
  ips.index_level,
  ips.page_count,
  ips.record_count,
  ips.avg_page_space_used_in_percent,
  ips.forwarded_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED') AS ips
ORDER BY ObjectName, index_id, index_level DESC;
```

---

### 🔦 Welche Heaps besitzen Forwarded Records?

```sql
SELECT
  OBJECT_NAME(object_id) AS HeapName,
  forwarded_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, 0, NULL, 'SAMPLED')
WHERE index_id = 0
  AND forwarded_record_count > 0
ORDER BY forwarded_record_count DESC;
```

---

## 🧪 Lab: HOBTs in Aktion (Copy & Paste)

```sql
USE tempdb;
GO

IF OBJECT_ID('dbo.HobtDemo') IS NOT NULL DROP TABLE dbo.HobtDemo;
GO

-- 1️⃣ Start: HEAP
CREATE TABLE dbo.HobtDemo
(
  Id       INT IDENTITY(1,1) NOT NULL,
  K1       INT NOT NULL,
  Payload  VARCHAR(100) NULL
);
GO

INSERT dbo.HobtDemo(K1, Payload)
SELECT TOP (5000) ABS(CHECKSUM(NEWID())) % 100, REPLICATE('x', 50)
FROM sys.all_objects a CROSS JOIN sys.all_objects b;

-- HOBT dla heapa
SELECT p.hobt_id, p.partition_number, au.type_desc, au.total_pages, au.used_pages
FROM sys.partitions p
JOIN sys.allocation_units au ON au.container_id = p.hobt_id
WHERE p.object_id = OBJECT_ID('dbo.HobtDemo')
ORDER BY au.type_desc;

-- 2️⃣ Dodaj indeks nieklastrowany (drugi HOBT)
CREATE INDEX IX_HobtDemo_K1 ON dbo.HobtDemo(K1);

SELECT i.name, i.index_id, p.hobt_id
FROM sys.indexes i
JOIN sys.partitions p ON p.object_id = i.object_id AND p.index_id = i.index_id
WHERE i.object_id = OBJECT_ID('dbo.HobtDemo')
ORDER BY i.index_id;

-- 3️⃣ Zamień na indeks klastrowany (heap → B-tree)
CREATE CLUSTERED INDEX CX_HobtDemo_Id ON dbo.HobtDemo(Id);

SELECT i.name, i.index_id, p.hobt_id
FROM sys.indexes i
JOIN sys.partitions p ON p.object_id = i.object_id AND p.index_id = i.index_id
WHERE i.object_id = OBJECT_ID('dbo.HobtDemo')
ORDER BY i.index_id;

-- 4️⃣ Poziomy drzewa po zmianie
SELECT ips.index_type_desc, ips.index_level, ips.page_count, ips.record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.HobtDemo'), NULL, NULL, 'DETAILED') ips
ORDER BY index_level DESC;
```

> 🔎 Beim Umwandeln eines Heaps in einen Clustered Index können sich Seitenlayout und Kennungen wie `hobt_id` ändern. Das ist normal.

---

## 🧭 Physischer Speicherort einer Zeile (RID / Clustered Key)

```sql
SELECT TOP (10)
  %%physloc%% AS FilePageSlot,
  sys.fn_PhysLocFormatter(%%physloc%%) AS Formatted,
  *
FROM dbo.HobtDemo
ORDER BY Id;
```

Wenn du tiefer einsteigen möchtest (im Lab, **Vorsicht in Produktion**):

```sql
DBCC TRACEON(3604);
-- DBCC PAGE (db_id, file_id, page_id, printopt)
-- DBCC IND (DB_ID(), 'dbo.HobtDemo', 1);
```

---

## 🚨 Typische Warnzeichen und Maßnahmen

### 1️⃣ Heap mit Forwarded Records

- Symptom: `forwarded_record_count > 0`.
- Auswirkung: zusätzliche Seitensprünge und I/O.
- Maßnahme: Heap mit `ALTER TABLE ... REBUILD` neu aufbauen oder einen geeigneten Clustered Key erwägen.

### 2️⃣ Ein zu tiefer Baum

- Symptom: hoher `index_level` und großer `page_count`.
- Auswirkung: mehr Zugriffe auf Zwischenebenen.
- Maßnahme: Schlüsselentwurf, Fill Factor, Partitionierung und Komprimierung prüfen.

### 3️⃣ Übermäßig viele ROW_OVERFLOW- / LOB-Daten

- Symptom: große `ROW_OVERFLOW_DATA`- oder `LOB_DATA`-Zuordnungen.
- Auswirkung: zusätzliche Lesezugriffe.
- Maßnahme: Spaltendesign prüfen, selten benötigte Attribute auslagern und Komprimierung erwägen.

---

## 🧰 DBA-Checkliste (HOBT-aware)

- HOBTs mit `sys.partitions` und `sys.allocation_units` inventarisieren.
- Baumebenen und Fragmentierung mit `sys.dm_db_index_physical_stats` prüfen.
- Heaps mit Forwarded Records ermitteln.
- Allocation Units messen (`IN_ROW_DATA`, `ROW_OVERFLOW_DATA`, `LOB_DATA`).
- Geeignete `REBUILD`- oder `REORGANIZE`-Maßnahmen planen.
- `page_count`, Forwarded Records und Seitendichte in Grafana überwachen.

---

## 🧩 Beispiel-View: `dbo.vHobtHealth`

```sql
CREATE OR ALTER VIEW dbo.vHobtHealth AS
SELECT
  DB_NAME()                         AS DbName,
  OBJECT_SCHEMA_NAME(p.object_id)   AS SchemaName,
  OBJECT_NAME(p.object_id)          AS ObjectName,
  i.index_id,
  ISNULL(i.name, '(HEAP)')          AS IndexName,
  p.partition_number,
  p.hobt_id,
  au_in.total_pages                 AS InRowPages,
  au_ro.total_pages                 AS RowOverflowPages,
  au_lob.total_pages                AS LobPages,
  ips.page_count,
  ips.record_count,
  ips.index_level,
  ips.avg_page_space_used_in_percent,
  ips.forwarded_record_count
FROM sys.partitions p
LEFT JOIN sys.indexes i ON i.object_id = p.object_id AND i.index_id = p.index_id
OUTER APPLY (SELECT SUM(total_pages) AS total_pages FROM sys.allocation_units WHERE container_id = p.hobt_id AND type_desc='IN_ROW_DATA') au_in
OUTER APPLY (SELECT SUM(total_pages) AS total_pages FROM sys.allocation_units WHERE container_id = p.hobt_id AND type_desc='ROW_OVERFLOW_DATA') au_ro
OUTER APPLY (SELECT SUM(total_pages) AS total_pages FROM sys.allocation_units WHERE container_id = p.hobt_id AND type_desc='LOB_DATA') au_lob
OUTER APPLY (SELECT TOP (1) *
  FROM sys.dm_db_index_physical_stats(DB_ID(), p.object_id, p.index_id, p.partition_number, 'SAMPLED')
) ips;
GO
```

---

## 🧭 Zusammenfassung

**HOBT** ist der Punkt, an dem **logische Indexorganisation auf die Physik der Seiten trifft**. Wer `hobt_id` und die zugehörigen Allocation Units versteht, kann:

- nachvollziehen, wo Zeilen gespeichert sind,
- Forwarded Records, Baumtiefe und Fragmentierung diagnostizieren,
- Clustered Keys und Partitionen bewusster entwerfen.

---

## 🔧 TL;DR: Werkzeuge

| Ziel | DMV / Funktion |
|---|---|
| Seitenzuordnung | `sys.partitions.hobt_id ⇄ sys.allocation_units.container_id` (für IN_ROW_DATA / ROW_OVERFLOW_DATA) |
| Physische Statistiken | `sys.dm_db_index_physical_stats` |
| Seitenzuordnung im Detail | `sys.dm_db_database_page_allocations` |
| Speicherort einer Zeile | `%%physloc%%`, `fn_PhysLocFormatter` |
| Seitendiagnose (Lab) | `DBCC IND`, `DBCC PAGE` |

---
