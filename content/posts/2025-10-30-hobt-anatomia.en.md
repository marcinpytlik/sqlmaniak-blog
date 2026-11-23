---
title: "HOBT: The Hierarchy of Data Organization"
date: 2025-10-30
slug: hobt-anatomia
tags: [SQLServer, Internals, Indexes, HOBT, Storage]
draft: false
---

Data in SQL Server does not lie around randomly. It forms structures whose branches lead to data pages. **HOBT (Heap Or B-Tree)** is the storage structure behind each B-tree index and heap table. It is the skeleton of data organization and addressing — from the *root*, through intermediate levels, down to the *leaf* pages of a B-tree.

> “Structure is the form in which order exists.” — SQLManiak

---

## 🧩 What is a HOBT in practice?

Each partition of an index or heap has **one HOBT** (a table with one partition and three indexes has four HOBTs; a table with four partitions and two indexes has eight).

**HOBT is not the same as an index object**: it describes the physical structure for a particular index or heap partition.

🆔 **HOBT identifier:** `hobt_id` — associated with the structure during its lifetime, but it can change after certain rebuild operations.

---

## 📦 HOBTs and allocation units

A HOBT-related partition may use up to **three allocation-unit types**:

- **IN_ROW_DATA** — rows stored in regular 8 KB data pages.
- **ROW_OVERFLOW_DATA** — variable-length data moved off-row when the row exceeds the in-row limit.
- **LOB_DATA** — large objects such as XML and `VARBINARY(MAX)`.

📎 Relationship:
`sys.allocation_units.container_id = sys.partitions.hobt_id` for IN_ROW_DATA and ROW_OVERFLOW_DATA; LOB_DATA uses the partition identifier instead.

---

## 🌲 Heaps versus B-trees

**Heap:**
- no clustered index key,
- data pages are **not logically ordered** by a clustered key,
- updates that enlarge rows can create *forwarded records*.

**B-tree index:**
- ordered index structure,
- clustered index leaf level contains the table's data rows,
- nonclustered index leaf level contains keys and row locators (`RID` or clustered key).

---

## 🗺️ Page maps and metadata

**Metadata and allocation maps:** `PFS` (Page Free Space), `GAM`/`SGAM` (extent allocation), and `IAM` (Index Allocation Map) connect storage structures to allocated pages.

**Tree diagnostics:**
- `sys.dm_db_index_physical_stats` — levels, fragmentation, forwarded records,
- `sys.dm_db_database_page_allocations` — allocation details (undocumented),
- `DBCC PAGE/IND` — deeper inspection (undocumented).

---

## 🔍 Quick DMVs: HOBTs in your database

### 📘 HOBT overview

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

### 📊 Tree levels and physical statistics

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

### 🔦 Which heaps have forwarded rows?

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

## 🧪 Lab: See HOBTs in action (copy and paste)

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

> 🔎 After converting a heap into a clustered index, page layout and identifiers such as `hobt_id` may change. That is expected.

---

## 🧭 Physical row location (RID / clustered key)

```sql
SELECT TOP (10)
  %%physloc%% AS FilePageSlot,
  sys.fn_PhysLocFormatter(%%physloc%%) AS Formatted,
  *
FROM dbo.HobtDemo
ORDER BY Id;
```

If you want to go deeper (in a lab, **use caution in production**):

```sql
DBCC TRACEON(3604);
-- DBCC PAGE (db_id, file_id, page_id, printopt)
-- DBCC IND (DB_ID(), 'dbo.HobtDemo', 1);
```

---

## 🚨 Common warning signs and remedies

### 1️⃣ Heap with forwarded records

- Symptom: `forwarded_record_count > 0`.
- Impact: additional page hops and I/O.
- Remedy: rebuild the heap with `ALTER TABLE ... REBUILD`, or consider an appropriate clustered key.

### 2️⃣ An overly deep tree

- Symptom: high `index_level` and large `page_count`.
- Impact: more intermediate page reads.
- Remedy: review the key design, fill factor, partitioning, and compression.

### 3️⃣ Excessive ROW_OVERFLOW / LOB data

- Symptom: large `ROW_OVERFLOW_DATA` or `LOB_DATA` allocations.
- Impact: additional reads.
- Remedy: review column design, separate rarely accessed attributes, and consider compression.

---

## 🧰 DBA checklist (HOBT-aware)

- Inventory HOBTs with `sys.partitions` and `sys.allocation_units`.
- Review tree levels and fragmentation with `sys.dm_db_index_physical_stats`.
- Identify heaps with forwarded records.
- Measure allocation units (`IN_ROW_DATA`, `ROW_OVERFLOW_DATA`, `LOB_DATA`).
- Plan appropriate `REBUILD` or `REORGANIZE` operations.
- Monitor `page_count`, forwarded records, and page density in Grafana.

---

## 🧩 Example view: `dbo.vHobtHealth`

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

## 🧭 Summary

**HOBT** is where **logical index organization meets the physics of pages**. By understanding `hobt_id` and related allocation units, you can:

- understand where rows are stored,
- diagnose forwarded records, tree depth, and fragmentation,
- design clustered keys and partitions more deliberately.

---

## 🔧 TL;DR: Tools

| Goal | DMV / function |
|---|---|
| Map pages | `sys.partitions.hobt_id ⇄ sys.allocation_units.container_id` (for IN_ROW_DATA / ROW_OVERFLOW_DATA) |
| Physical statistics | `sys.dm_db_index_physical_stats` |
| Page allocations | `sys.dm_db_database_page_allocations` |
| Row location | `%%physloc%%`, `fn_PhysLocFormatter` |
| Page diagnostics (lab) | `DBCC IND`, `DBCC PAGE` |

---
