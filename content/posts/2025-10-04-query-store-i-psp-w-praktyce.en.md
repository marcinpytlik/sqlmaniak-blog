---
title: "Query Store and Parameter Sensitive Plan (PSP): Real-World Exercises"
date: "2025-10-04"
slug: "query-store-and-psp-in-practice"
draft: false
description: "A practical PSP guide: exploring plans for different parameter selectivity ranges, stabilizing them, and diagnosing regressions in Query Store."
tags: ["SQL Server","Query Store","PSP","Performance","Tuning"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/query-store-i-psp-w-praktyce.png"
---

Lead
----
PSP is a remedy for the problem of one parameter value dictating the plan for everyone. Here is a demo: three selectivity ranges, three plans, no drama.

## Setup
```sql
USE tempdb;
DROP TABLE IF EXISTS dbo.Sales;
CREATE TABLE dbo.Sales (
  Id int IDENTITY primary key,
  CustomerId int not null,
  Amount money not null,
  CreatedAt datetime2 not null,
  filler char(200) null
);
CREATE INDEX IX_Sales_CustomerId ON dbo.Sales(CustomerId);
-- Dane z rozkładem Zipfa – część klientów bardzo „ciężka”
WITH n AS (SELECT TOP (1000000) ROW_NUMBER() OVER(ORDER BY (SELECT 1)) AS n FROM sys.all_objects a, sys.all_objects b)
INSERT dbo.Sales(CustomerId, Amount, CreatedAt, filler)
SELECT ABS(CHECKSUM(NEWID()))%1000, RAND(CHECKSUM(NEWID()))*100, DATEADD(day, -ABS(CHECKSUM(NEWID()))%365, SYSDATETIME()), NULL FROM n;
```

Enable PSP (ON by default in newer CUs):
```sql
ALTER DATABASE SCOPED CONFIGURATION SET PARAMETER_SENSITIVE_PLAN_OPTIMIZATION = ON;
```

## Test
```sql
CREATE OR ALTER PROC dbo.GetSalesByCustomer @CustomerId int AS
SELECT * FROM dbo.Sales WHERE CustomerId=@CustomerId OPTION (RECOMPILE OFF);
GO
EXEC dbo.GetSalesByCustomer @CustomerId=1;     -- rzadki
EXEC dbo.GetSalesByCustomer @CustomerId=500;   -- średni
EXEC dbo.GetSalesByCustomer @CustomerId=999;   -- „gorący”
```

In Query Store, inspect `sys.query_store_plan` to find plan variants for different selectivity buckets.

## Stabilization when needed
- Use the `OPTIMIZE FOR (@CustomerId UNKNOWN)` hint when you prefer a more robust plan.  
- Force a plan in Query Store if a regression occurs after a CU update.

## What to monitor
- Number of *variant plans* per query.  
- Execution time and CPU regressions after deployment.  
- Whether PSP produces too many plans for ad hoc queries.

> PSP is not a silver bullet — sometimes a new index or refactoring the predicate is better.
