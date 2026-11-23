---
title: "Query Store und Parameter Sensitive Plan (PSP): Übungen aus der Praxis"
date: "2025-10-04"
slug: "query-store-und-psp-in-der-praxis"
draft: false
description: "Praxisleitfaden zu PSP: Pläne für verschiedene Parameterselektivitäten untersuchen, stabilisieren und Regressionen im Query Store erkennen."
tags: ["SQL Server","Query Store","PSP","Performance","Tuning"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/query-store-i-psp-w-praktyce.png"
---

Lead
----
PSP hilft gegen das Problem, dass ein einzelner Parameterwert den Ausführungsplan für alle bestimmt. Hier kommt eine Demo: drei Selektivitätsbereiche, drei Pläne, kein Drama.

## Einrichtung
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

PSP aktivieren (in neueren CUs standardmäßig eingeschaltet):
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

Prüfe im Query Store `sys.query_store_plan`: Dort lassen sich Planvarianten für verschiedene Selektivitätsbereiche erkennen.

## Stabilisierung bei Bedarf
- Verwende den Hint `OPTIMIZE FOR (@CustomerId UNKNOWN)`, wenn du einen robusteren Plan bevorzugst.  
- Erzwinge bei einer Regression nach einem CU-Update einen Plan im Query Store.

## Was überwacht werden sollte
- Anzahl der *Planvarianten* pro Abfrage.  
- Regressionen bei Laufzeit und CPU nach einem Deployment.  
- Ob PSP zu viele Pläne für Ad-hoc-Abfragen erzeugt.

> PSP ist kein Allheilmittel — manchmal sind ein neuer Index oder die Überarbeitung des Filters die bessere Lösung.
