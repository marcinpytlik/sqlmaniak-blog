---
title: "Was verursacht Parameter Sniffing in SQL Server?"
date: 2025-11-11
slug: parameter-sniffing
tags: [SQLServer, Performance, Query Processor, PSPO, Execution Plans]
draft: false
---

# Was verursacht *Parameter Sniffing* in SQL Server?

*Ein Mechanismus, der Abfragen beschleunigen — oder ihre Performance massiv verschlechtern kann.*

## Einführung

SQL Server kann dieselbe Abfrage auf zwei völlig unterschiedliche Arten ausführen: einmal blitzschnell, ein anderes Mal extrem langsam. Die Ursache ist häufig **Parameter Sniffing**.

Es gehört zu den häufigsten Performanceproblemen und ist gleichzeitig eine der nützlichsten Optimierungen des Query Processors. Wer versteht, wie Sniffing entsteht, kann instabile Ausführungspläne besser diagnostizieren.

## Was ist *Parameter Sniffing*?

Wenn eine Abfrage Parameter verwendet, beispielsweise in einer Stored Procedure, **liest SQL Server den Parameterwert bei der Kompilierung des Ausführungsplans**. Der zuerst „erschnüffelte“ Wert dient dem Optimizer dazu:

- die Kardinalität zu schätzen,
- zwischen Index Seek und Scan zu wählen,
- Join-Typen und Join-Reihenfolge festzulegen,
- Operatoren wie Nested Loops oder Hash Match auszuwählen.

Ein für den ersten Aufruf kompilierter Plan kann im **Plan Cache** gespeichert und für spätere Aufrufe wiederverwendet werden — selbst wenn deren Parameterwerte völlig anders sind.

## Wann wird *Parameter Sniffing* zum Problem?

Der Mechanismus ist oft vorteilhaft, solange **die Datenverteilung einigermaßen gleichmäßig ist**. Probleme beginnen, wenn:

- die erste Ausführung einen „kleinen“ Parameter verwendet (ein seltener Kunde mit nur 15 Zeilen),
- die zweite Ausführung einen „großen“ Parameter verwendet (ein Großkunde mit 15.000.000 Zeilen),

und SQL Server **weiterhin denselben gemeinsamen Plan verwendet**.

Die Folgen:

- Ein für kleine Ergebnismengen optimierter Plan kann bei großen Mengen katastrophal sein.
- Ein für große Mengen optimierter Plan kann bei kleinen Mengen überdimensioniert sein.
- Die Last ändert sich im Tagesverlauf dynamisch.

## Was verursacht *Parameter Sniffing* tatsächlich?

### ✅ Hauptursache: Unterschiedliche Parameterwerte für dieselbe Abfrage

**Der bei der ersten Kompilierung verfügbare Parameterwert** beeinflusst, welcher Plan in den Cache gelangt. Bei schiefer Datenverteilung können spätere Ausführungen den Plan unter ungünstigen Bedingungen wiederverwenden.

Das Grundproblem ist nicht einfach die Anzahl der Indizes, Zeilen oder der verfügbare Speicher, sondern das Zusammenspiel von **Parameterwerten, Datenverteilung, Kardinalitätsschätzung und Planwiederverwendung**.

## Warum macht SQL Server das?

Weil es in vielen Fällen eine gute Strategie ist.

Sniffing erlaubt dem Query Processor, einen Plan für einen konkreten Parameterwert zu optimieren, statt immer einen generischen Plan zu wählen, der für viele Ausführungen langsamer wäre.

Es funktioniert gut, wenn:

- die Daten relativ gleichmäßig verteilt sind,
- sich die Verteilung nicht drastisch ändert,
- Parameterwerte keine um Größenordnungen unterschiedlichen Zeilenzahlen liefern.

Es funktioniert schlecht, wenn:

- die Verteilung stark schief ist,
- einige Werte selten und andere extrem häufig sind,
- der gecachte Plan nicht zum aktuellen Wert passt.

## Wie lässt sich das diagnostizieren?

Typische Symptome:

- Dieselbe Abfrage dauert einmal 50 ms und ein anderes Mal 20 Sekunden.
- Die Laufzeit hängt stark vom Parameterwert ab.
- Pläne unterscheiden sich bei Seeks, Scans, Joins und anderen Operatoren.
- Im Actual Execution Plan bestehen möglicherweise große Unterschiede zwischen **Estimated Rows** und **Actual Rows**.

## Wie lassen sich negative Auswirkungen begrenzen?

Häufige Techniken:

- **`OPTION (RECOMPILE)`** — die Anweisung bei jeder Ausführung neu kompilieren.
- **`OPTIMIZE FOR (@param = …)`** — für einen bestimmten Wert optimieren.
- **`OPTIMIZE FOR UNKNOWN`** — Schätzungen verwenden, die den aktuellen Parameterwert nicht sniffen.
- **Prozeduren oder Ausführungspfade aufteilen** — kleine und große Workloads trennen.
- **PSP Optimization (SQL Server 2022)** — geeignete Abfragen können mehrere Planvarianten für unterschiedliche Parameterbereiche erhalten.

---

## T-SQL-Demo

Die Demo erstellt eine Datenbank mit schiefer Datenverteilung, eine parametrisierte Prozedur und Beispiele dafür, wie der erste Parameterwert den gecachten Plan beeinflussen kann.

Das folgende Lab-Skript wurde **unverändert aus dem polnischen Original übernommen**, einschließlich Kommentaren und experimentellen Query-Store-Abschnitten. Prüfe es vor der Ausführung: Es löscht eine Demo-Datenbank, und einige Query-Store-Hint-Beispiele müssen möglicherweise an den jeweiligen SQL-Server-Build angepasst werden.

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

## Zusammenfassung

*Parameter Sniffing* ist kein Fehler, sondern ein Mechanismus.

Probleme entstehen, wenn **verschiedene Parameterwerte sehr unterschiedliche Datenverteilungen aufweisen und ein gecachter Plan wiederverwendet wird**.

**Die richtige Quizantwort lautet:** *Unterschiedliche Parameterwerte können unterschiedliche Pläne benötigen, die Ausführung verwendet jedoch möglicherweise einen gemeinsamen gecachten Plan.*

Sniffing zu verstehen ist eine Grundlage der Arbeit mit dem Query Processor.
