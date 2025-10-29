---
title: "Query Store i Parameter Sensitive Plan (PSP): ćwiczenia z życia"
date: "2025-10-04"
slug: "query-store-i-psp-w-praktyce"
draft: false
description: "Praktyczny przewodnik po PSP: jak zobaczyć trzy plany dla różnych zakresów parametrów, jak je stabilizować i jak diagnozować regresje w Query Store."
tags: ["SQL Server", "Query Store", "PSP", "Performance", "Tuning"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/query-store-i-psp-w-praktyce.png"
canonical: "https://sqlmaniak.blog/query-store-i-psp-w-praktyce"
---

Lead
----
PSP to lekarstwo na „jeden parametr rządzi wszystkimi”. Pokażę Ci demo: trzy przedziały selektywności, trzy plany, zero dramatu.

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

Włącz PSP (domyślnie ON w nowszych CU):
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

W Query Store sprawdź: `sys.query_store_plan` – pojawią się warianty planów na różne „bucket’y” selektywności.

## Stabilizacja gdy trzeba
- Hint `OPTIMIZE FOR (@CustomerId UNKNOWN)` gdy wolisz plan „robust”.  
- Plan forcing w Query Store, jeśli regresja po CU.

## Co monitorować
- Liczba *variant plans* na zapytanie.  
- Regresje czasu/CPU po deployu.  
- Czy PSP nie generuje nadmiaru planów dla zapytań ad‑hoc.

> PSP to nie srebrna kula — czasem lepszy jest nowy indeks lub refaktoryzacja filtra.
