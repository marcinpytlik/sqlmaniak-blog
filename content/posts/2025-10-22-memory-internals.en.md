---
title: "SQL Server Memory Internals: What Happens in the Buffer Pool"
date: 2025-10-22
slug: memory-internals
tags: [SQLServer, Internals, Memory, Performance, DBA]
draft: false
---

Behind every operation lies memory: **Buffer Pool**, **Memory Clerks**, **Lazy Writer**, and **PLE (Page Life Expectancy)**. They are at the heart of SQL Server, and a sharp PLE drop can be a warning sign. Understanding how SQL Server manages data pages is essential for meaningful tuning.

> “What does not fit in memory will come back from disk for revenge.”

---

## 🧠 SQL Server memory architecture

SQL Server has its own memory-management mechanisms, working alongside the operating system. This lets it respond to workload demands and manage internal allocations.

The main components:

| Area | Description |
|---|---|
| **Buffer Pool** | Caches 8 KB data pages, supporting reads and writes. |
| **Plan Cache** | Stores compiled query plans; excessive plan cache usage can compete with other memory consumers. |
| **Memory Clerks** | Track memory allocations for SQL Server subsystems. |
| **Workspace Memory** | Memory used by operations such as sorts, hash joins, and aggregations. |
| **Stolen Memory** | Buffer-pool-managed memory allocated to purposes other than caching database pages. |

---

## 🔄 How SQL Server manages pages

A data page may pass through several stages:

1. **Physical Read** — the page is read from disk into the Buffer Pool.
2. **Use in Query** — a query accesses the cached page.
3. **Dirty Page** — the page has been modified but has not yet been written to disk.
4. **Checkpoint / Lazy Writer** — background mechanisms write dirty pages when appropriate.
5. **Eviction (LRU)** — pages may be removed from the cache when memory is needed.

SQL Server uses an **LRU-like (Least Recently Used)** replacement policy, together with other mechanisms, to decide which pages can be evicted.

---

## 📊 Key indicators

| Indicator | Meaning |
|---|---|
| **Page Life Expectancy (PLE)** | Approximate time a page remains in the cache. Sustained declines may indicate memory pressure. |
| **Lazy Writes/sec** | Number of pages written by Lazy Writer per second. |
| **Memory Grants Pending** | Queries waiting for workspace memory grants. |
| **Target vs Total Server Memory** | How SQL Server's current memory use compares with its target. |
| **Memory Clerks** | Which subsystems are consuming memory, such as the Buffer Pool, query execution, or lock manager. |

---

## 🧩 Step-by-step diagnostics

📁 The repository includes ready-to-use scripts:

| Script | Description |
|---|---|
| `Target_vs_Total_Server_Memory.sql` | Compare target and total server memory. |
| `BufferPool_PLE_Counters.sql` | PLE trends by NUMA node. |
| `Memory_Clerks_Overview.sql` | Identify the largest memory consumers. |
| `Memory_Grants_Status.sql` | Find queries waiting for memory grants. |
| `LazyWriter_Checkpoint_Stats.sql` | Background write activity. |
| `BufferPool_ModifiedPages.sql` | Dirty pages per database. |
| `Waits_Memory_Pressure.sql` | Investigate waits associated with memory pressure. |
| `PLE_Trend_Collector_Proc.sql` | Collect PLE trends over time. |

---

## 🧠 Query Store Hints: a tool for unstable grants

SQL Server 2022 lets you apply optimizer hints **without changing application code**. You can use this to limit excessive memory grants, stabilize plans, and influence optimizer behavior.

```sql
EXEC sys.sp_query_store_set_hints
    @query_id = 12345,
    @value = N'OPTION(MAX_GRANT_PERCENT = 5)';
```

To undo the change:

```sql
EXEC sys.sp_query_store_remove_hints @query_id = 12345;
```

---

## 📈 Treat PLE as a trend, not a number

A single PLE reading rarely tells the whole story — the **trend** matters. That is why the repository includes a collector that samples values at intervals and stores them in `dbo.PLE_History`.

The result is a history of memory behavior that you can plot in Excel or Grafana.

```sql
EXEC dbo.CollectPLETrend @Samples = 120, @IntervalSeconds = 10;
```

---

## 🧭 Good practices

- Do not add RAM before understanding **who is consuming it**.
- Treat **PLE as a trend**, not an isolated number.
- Observe **Memory Clerks**, not just overall memory use.
- **Plan cache** also consumes memory; good parameterization matters.
- Use **Query Store Hints** to influence plans when you cannot change the application code.

> “Performance begins with understanding what really occupies memory.”

---

📘 Repository: [github.com/marcinpytlik/SQLManiak/tree/master/docs/MemoryInternals](https://github.com/marcinpytlik/SQLManiak/tree/master/docs/MemoryInternals)
