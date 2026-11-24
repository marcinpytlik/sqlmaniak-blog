---
title: "What Causes Parameter Sniffing in SQL Server?"
date: 2025-11-11
slug: parameter-sniffing
tags: [SQLServer, Performance, Query Processor, PSPO, Execution Plans]
draft: false
---

# What Causes *Parameter Sniffing* in SQL Server?

*A mechanism that can accelerate a query — or destroy its performance.*

## Introduction

SQL Server can execute the same query in two completely different ways: extremely quickly one time and dramatically slowly the next. The cause is often **parameter sniffing**.

This is one of the most common performance issues and, at the same time, one of the most useful Query Processor optimizations. Understanding where sniffing comes from is essential when diagnosing unstable execution plans.

## What Is *Parameter Sniffing*?

When a query uses parameters, for example in a stored procedure, SQL Server **reads the parameter value when compiling the execution plan**. The value it first “sniffs” is used by the optimizer to:

- estimate cardinality,
- select an access strategy (index seek versus scan),
- choose join types and join order,
- select operators such as Nested Loops or Hash Match.

A plan compiled for the initial invocation may be stored in the **plan cache** and reused for later calls, even when their parameter values are very different.

## When Does *Parameter Sniffing* Become a Problem?

The mechanism is often beneficial when **data distribution is reasonably uniform**. Problems begin when:

- the first execution uses a “small” parameter (a rare customer returning only 15 rows),
- the second uses a “large” parameter (a wholesale customer returning 15,000,000 rows),

and SQL Server **continues to reuse one shared plan**.

As a result:

- a plan optimized for a small result set can perform disastrously on a large one,
- a plan optimized for a large result set can be excessive for a small one,
- the workload changes dynamically during the day.

## What Actually Causes *Parameter Sniffing*?

### ✅ Main Cause: Different Parameter Values for the Same Query

**The parameter value available during initial compilation** influences which plan enters the cache. If data is skewed, later executions may reuse that plan under unsuitable conditions.

The underlying issue is not simply the number of indexes, rows, or available memory: it is the interaction between **parameter values, data distribution, cardinality estimates, and plan reuse**.

## Why Does SQL Server Do This?

Because in many cases it is a good strategy.

Sniffing allows the Query Processor to optimize for a specific parameter value rather than always choosing a generic plan that might be slower for many executions.

It works well when:

- data is relatively uniform,
- distributions do not change drastically,
- parameter values do not produce row counts that differ by orders of magnitude.

It works poorly when:

- the distribution is highly skewed,
- some values are rare and others extremely common,
- the cached plan is a poor fit for the current value.

## How Can You Diagnose It?

Typical symptoms:

- the same query sometimes takes 50 ms and sometimes 20 seconds,
- runtime depends strongly on the parameter value,
- plan choices differ between seeks, scans, joins, and other operators,
- the Actual Execution Plan may show large differences between **Estimated Rows** and **Actual Rows**.

## How Can You Mitigate the Negative Effects?

Common techniques include:

- **`OPTION (RECOMPILE)`** — compile a statement again for each execution.
- **`OPTIMIZE FOR (@param = …)`** — optimize for a selected value.
- **`OPTIMIZE FOR UNKNOWN`** — use estimates that do not sniff the current parameter value.
- **Split procedures or branches** — separate paths for small and large workloads.
- **PSP Optimization (SQL Server 2022)** — eligible queries may have multiple plan variants selected for different parameter ranges.

---

## T-SQL Demo

In short, the demo creates a database with skewed data, a parameterized procedure, and examples illustrating how the initial parameter value can affect the cached plan.

The following lab script is preserved **verbatim from the Polish original**, including its comments and experimental Query Store sections. Review it before running: it drops a demo database, and some Query Store hint examples may need correction for the target SQL Server build.

```sql
/*
    demo_parameter_sniffing.sql
    Autor: SQLManiak
    Cel: Zademonstrować zjawisko parameter sniffing i metody przeciwdziałania.

    Wymagania: SQL Server 2016+ (PSPO sekcja opcjonalna dla 2022)
*/

-- 0) Sprzątanie (uruchamiaj świadomie w środowisku demo)
IF DB_ID('ParameterSniffingDemo') IS NOT NULL
BEGIN
    ALTER DATABASE ParameterSniffingDemo SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE ParameterSniffingDemo;
END
GO

-- 1) Baza i obiekty
CREATE DATABASE ParameterSniffingDemo;
GO
-- Dla PSPO (SQL Server 2022). W starszych wersjach ustaw 140/150.
ALTER DATABASE ParameterSniffingDemo SET COMPATIBILITY_LEVEL = 160; 
GO
USE ParameterSniffingDemo;
GO

CREATE TABLE dbo.Orders
(
    OrderID      BIGINT IDENTITY(1,1) PRIMARY KEY,
    CustomerID   INT            NOT NULL,
    OrderDate    DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),
    Amount       MONEY          NOT NULL
);
GO

-- Indeks wspierający wyszukiwanie po CustomerID
CREATE INDEX IX_Orders_CustomerID ON dbo.Orders(CustomerID) INCLUDE (Amount, OrderDate);
GO

-- 2) Dane z rozkładem skośnym (skew)
--   - Większość klientów ma ~50–100 wierszy
--   - Jeden "gorący" klient ma setki tysięcy wierszy
SET NOCOUNT ON;

;WITH nums AS
(
    SELECT TOP (50000) ROW_NUMBER() OVER (ORDER BY (SELECT 0)) AS n
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT INTO dbo.Orders (CustomerID, OrderDate, Amount)
SELECT (ABS(CHECKSUM(NEWID())) % 10000) + 1,     -- 10k klientów "zwykłych"
       DATEADD(DAY, -ABS(CHECKSUM(NEWID())) % 365, SYSUTCDATETIME()),
       1.0 + (ABS(CHECKSUM(NEWID())) % 1000) / 10.0
FROM nums;

-- "Gorący" klient: 42
;WITH nums AS
(
    SELECT TOP (400000) ROW_NUMBER() OVER (ORDER BY (SELECT 0)) AS n
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT INTO dbo.Orders (CustomerID, OrderDate, Amount)
SELECT 42,
       DATEADD(DAY, -ABS(CHECKSUM(NEWID())) % 365, SYSUTCDATETIME()),
       1.0 + (ABS(CHECKSUM(NEWID())) % 1000) / 10.0
FROM nums;

-- Statystyki
UPDATE STATISTICS dbo.Orders WITH FULLSCAN;
GO

-- 3) Procedura z parametrem (klasyczny kandydat do sniffingu)
CREATE OR ALTER PROC dbo.GetOrdersByCustomer
    @CustomerID INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT OrderID, CustomerID, OrderDate, Amount
    FROM dbo.Orders
    WHERE CustomerID = @CustomerID;
END
GO

-- 4) Narzędzia: czyść cache, żeby wymusić kompilację
-- Uwaga: Czyści plany dla całej bazy (tu: tylko demo)
ALTER DATABASE SCOPED CONFIGURATION CLEAR PROCEDURE_CACHE;
GO

-- 5) SCENARIUSZ A: najpierw "rzadki" klient → plan optymalny pod mały wynik
DECLARE @rare INT = 7777; -- rzadki klient (~kilkadziesiąt wierszy)
EXEC dbo.GetOrdersByCustomer @CustomerID = @rare;

-- Kolejne wywołanie na "gorącym" kliencie może użyć NIEoptymalnego planu
EXEC dbo.GetOrdersByCustomer @CustomerID = 42;
GO

-- 6) Wyczyść cache i odwróć kolejność
ALTER DATABASE SCOPED CONFIGURATION CLEAR PROCEDURE_CACHE;
GO

-- Najpierw "gorący" klient → plan optymalny pod duży wynik
EXEC dbo.GetOrdersByCustomer @CustomerID = 42;

-- Teraz rzadki: może trafić plan z nadmiarem (np. skan/hash)
EXEC dbo.GetOrdersByCustomer @CustomerID = 7777;
GO

/* Obserwacje:
   - Porównaj rzeczywiste plany wykonania (Actual Execution Plan) między scenariuszami.
   - Różnice zobaczysz w operatorach (seek vs scan), joinach, IO, CPU.
*/

-- 7) Poskramianie sniffingu — warianty

-- 7.1 RECOMPILE (plan zawsze z bieżącym parametrem)
CREATE OR ALTER PROC dbo.GetOrders_Recompile
    @CustomerID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT OrderID, CustomerID, OrderDate, Amount
    FROM dbo.Orders
    WHERE CustomerID = @CustomerID
    OPTION (RECOMPILE);
END
GO

EXEC dbo.GetOrders_Recompile @CustomerID = 42;
EXEC dbo.GetOrders_Recompile @CustomerID = 7777;
GO

-- 7.2 OPTIMIZE FOR UNKNOWN (plan uśredniony z histogramu)
CREATE OR ALTER PROC dbo.GetOrders_Unknown
    @CustomerID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT OrderID, CustomerID, OrderDate, Amount
    FROM dbo.Orders
    WHERE CustomerID = @CustomerID
    OPTION (OPTIMIZE FOR UNKNOWN);
END
GO

EXEC dbo.GetOrders_Unknown @CustomerID = 42;
EXEC dbo.GetOrders_Unknown @CustomerID = 7777;
GO

-- 7.3 OPTIMIZE FOR konkretną wartość (np. dominującą)
CREATE OR ALTER PROC dbo.GetOrders_OptimizeForHot
    @CustomerID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT OrderID, CustomerID, OrderDate, Amount
    FROM dbo.Orders
    WHERE CustomerID = @CustomerID
    OPTION (OPTIMIZE FOR (@CustomerID = 42));
END
GO

EXEC dbo.GetOrders_OptimizeForHot @CustomerID = 42;     -- idealnie dla "gorącego"
EXEC dbo.GetOrders_OptimizeForHot @CustomerID = 7777;   -- może być nadmiarowy
GO

-- 8) (Opcjonalnie) SQL Server 2022 – PSPO (Parameter Sensitive Plan Optimization)
-- Wymaga level 160 (ustawiliśmy) i działa automatycznie jako część IQP.
-- Nie ma osobnego przełącznika dla pojedynczej procedury; to zachowanie optymalizatora.
-- Możesz obserwować, że do cache trafią różne "plan variants" w zależności od progu selektywności.

-- 9) Szybkie metryki pomocnicze (DMV)
SELECT TOP (20)
       cp.objtype, cp.usecounts, cp.size_in_bytes/1024 AS size_kb,
       st.text, qp.query_plan
FROM sys.dm_exec_cached_plans AS cp
CROSS APPLY sys.dm_exec_sql_text(cp.plan_handle) AS st
OUTER APPLY sys.dm_exec_query_plan(cp.plan_handle) AS qp
WHERE st.text LIKE '%GetOrders%'
ORDER BY cp.usecounts DESC;
GO

-- 10) Porządki (opcjonalnie)
-- DROP DATABASE ParameterSniffingDemo;


-----------------------------------------------------------------------
-- 7.4 Selektwność-świadoma procedura (branching po progach)
--     Idea: policz przybliżoną liczność dla parametru i wybierz właściwą strategię.
--     Uwaga: COUNT(*) + OPTION(RECOMPILE) służy tylko do sterowania progiem.
-----------------------------------------------------------------------
CREATE OR ALTER PROC dbo.GetOrders_SelectivityAware
    @CustomerID INT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @rowcount BIGINT;

    -- Szacujemy wolumen dla danego @CustomerID; RECOMPILE zapewnia rzeczywiste oszacowanie na bieżącym parametrze
    SELECT @rowcount = COUNT(*)
    FROM dbo.Orders
    WHERE CustomerID = @CustomerID
    OPTION (RECOMPILE);

    -- Próg selektywności (dobierz do swojego workloadu)
    DECLARE @threshold BIGINT = 5000;

    IF (@rowcount < @threshold)
    BEGIN
        -- Wysoka selektywność: wymuś użycie indeksu (seek), minimalizuj IO
        SELECT OrderID, CustomerID, OrderDate, Amount
        FROM dbo.Orders WITH (INDEX(IX_Orders_CustomerID))
        WHERE CustomerID = @CustomerID
        OPTION (RECOMPILE);  -- plan zależny od wartości parametru
    END
    ELSE
    BEGIN
        -- Niska selektywność: pozwól optymalizatorowi wybrać skan/strategię "hurtową"
        SELECT OrderID, CustomerID, OrderDate, Amount
        FROM dbo.Orders
        WHERE CustomerID = @CustomerID
        OPTION (RECOMPILE);
    END
END
GO

-- Przykłady
EXEC dbo.GetOrders_SelectivityAware @CustomerID = 42;      -- spodziewanie ścieżka "duża"
EXEC dbo.GetOrders_SelectivityAware @CustomerID = 7777;    -- spodziewanie ścieżka "mała"
GO

-----------------------------------------------------------------------
-- 7.5 SQL Server 2022 – Query Store Hints
--     Wymagane: Query Store włączony i przechwytywanie planów/zapytań
-----------------------------------------------------------------------
-- Włącz Query Store (konfiguracja przykładowa; dopasuj do polityk)
ALTER DATABASE ParameterSniffingDemo SET QUERY_STORE = ON;
ALTER DATABASE ParameterSniffingDemo SET QUERY_STORE (OPERATION_MODE = READ_WRITE);
GO

/* 
   Ustawienie Query Store Hint dla konkretnego tekstu zapytania wewnątrz procedury.
   UWAGA: OPTION(RECOMPILE) nie jest dozwolony jako Query Store hint (plan musi być re-używalny).
   Pokażemy dwa warianty:
     - OPTIMIZE FOR UNKNOWN (tworzy plan "uśredniony")
     - FORCESEEK (wymuszenie ścieżki indeksowej)
*/

-- a) OPTIMIZE FOR UNKNOWN przez Query Store Hint
EXEC sys.sp_query_store_set_hints
    @query_sql_text = N'
        SELECT OrderID, CustomerID, OrderDate, Amount
        FROM dbo.Orders
        WHERE CustomerID = @CustomerID
    ',
    @hint = N'OPTION (OPTIMIZE FOR (@CustomerID UNKNOWN))';
GO

-- b) FORCESEEK przez Query Store Hint (wymuszenie ścieżki indeksowej)
EXEC sys.sp_query_store_set_hints
    @query_sql_text = N'
        SELECT OrderID, CustomerID, OrderDate, Amount
        FROM dbo.Orders
        WHERE CustomerID = @CustomerID
    ',
    @hint = N'OPTION (FORCESEEK)';
GO

-- Sprawdzenie ustawionych hintów
SELECT qsq.query_text_id, qsq.query_sql_text, qsh.query_hint_id, qsh.query_hint_text, qsh.is_enabled
FROM sys.query_store_query_text AS qsq
JOIN sys.query_store_plan AS qsp ON qsq.query_text_id = qsp.query_text_id
JOIN sys.query_store_plan_hint AS qsh ON qsp.plan_id = qsh.plan_id
WHERE qsq.query_sql_text LIKE N'%FROM dbo.Orders%WHERE CustomerID = @CustomerID%';
GO

-- Usuwanie hintów (gdybyś chciał wrócić do defaultów)
EXEC sys.sp_query_store_clear_hints @query_sql_text = N'
        SELECT OrderID, CustomerID, OrderDate, Amount
        FROM dbo.Orders
        WHERE CustomerID = @CustomerID
';
GO


```

---

## Summary

*Parameter sniffing* is not a bug — it is a mechanism.

The problem arises when **different parameter values have very different data distributions and a cached plan is reused**.

**The correct quiz answer is:** *Different parameter values can require different plans, but execution may reuse a shared cached plan.*

Understanding sniffing is fundamental to working with the Query Processor.
