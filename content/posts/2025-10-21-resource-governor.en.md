---
title: "Resource Governor: Limit CPU, Not People"
date: 2025-10-21
slug: resource-governor
tags: [SQLServer, Performance, ResourceGovernor, TSQL, DBA]
draft: false
---

# Resource Governor: Limit CPU, Not People

Not every process deserves 100% of the CPU. Not every user should have an unrestricted highway to the cores. Resource Governor guards the balance by setting boundaries before chaos takes over.

SQL Server can be almost too accommodating. When a client application starts grinding through reports with spaghetti-like JOINs, the server may devote substantial resources to it while other users get stuck in traffic. Resource Governor says: *enough*.

This is not punishment; it is **fair allocation of computing resources**.

With Resource Governor, you can divide resources (CPU, memory, and I/O) between **workload groups** and assign sessions according to rules you define. Think of an open-plan office: each application gets its own desk, chair, and coffee allowance.

---

## ⚙️ How it works

1. **Resource Pools** define minimum and maximum allocations for CPU and memory. For example, `PoolReporty` is configured with 30% maximum CPU and 20% maximum memory.
2. **Workload Groups** associate sessions with specific pools. Reporting, OLTP, and test workloads each have their place.
3. **Classifier Function** is the heart of the mechanism: a T-SQL function that recognizes incoming connections and decides which group they belong to.

---

## 🧠 Configuration example

```sql
-- 1. Włącz Resource Governor
ALTER RESOURCE GOVERNOR RECONFIGURE;

-- 2. Utwórz Resource Pool
CREATE RESOURCE POOL PoolReporty
WITH (MAX_CPU_PERCENT = 30, MAX_MEMORY_PERCENT = 20);

-- 3. Utwórz Workload Group
CREATE WORKLOAD GROUP GrupaReporty
USING PoolReporty;

-- 4. Funkcja klasyfikująca
CREATE FUNCTION dbo.fnClassifier()
RETURNS sysname
WITH SCHEMABINDING
AS
BEGIN
    DECLARE @Group sysname;
    IF ORIGINAL_LOGIN() LIKE 'report%'
        SET @Group = 'GrupaReporty';
    ELSE
        SET @Group = 'default';
    RETURN @Group;
END;
GO

-- 5. Przypisz funkcję
ALTER RESOURCE GOVERNOR
WITH (CLASSIFIER_FUNCTION = dbo.fnClassifier);

ALTER RESOURCE GOVERNOR RECONFIGURE;
```

Now reporting users receive their share of CPU, leaving room for the rest of the server to breathe.

---

## 🔬 Verification

Inspect the DMVs:

```sql
SELECT pool_id, name, min_cpu_percent, max_cpu_percent
FROM sys.resource_governor_resource_pools;

SELECT group_id, name, pool_id
FROM sys.resource_governor_workload_groups;
```

You can also review execution statistics in `sys.dm_resource_governor_workload_groups` to identify workloads consuming the most resources.

---

## 🧩 A SQLManiak reflection

In the world of processes, everyone wants to be king of the CPU. But real balance does not come from brute force — it comes from **deliberate allocation**.

Resource Governor is a tool for the philosophical DBA: it teaches us that limits can be a condition for harmony.

> “Not every application is equal — but every application deserves its own 30% of CPU.”
