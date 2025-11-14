---
title: "Co powoduje parameter sniffing w SQL Server?"
date: 2025-11-11
slug: parameter-sniffing
tags: [SQLServer, Performance, Query Processor, PSPO, Execution Plans]
draft: false
---

# Co powoduje *parameter sniffing* w SQL Server?
*Mechanizm, który potrafi przyspieszyć zapytanie… albo zabić jego wydajność.*

## Wprowadzenie

SQL Server potrafi wykonać to samo zapytanie na dwa zupełnie różne sposoby — raz błyskawicznie, innym razem dramatycznie wolno. Przyczyną często jest zjawisko znane jako **parameter sniffing**.

To jeden z najczęstszych problemów wydajnościowych, a jednocześnie jedna z najgenialniejszych optymalizacji w Query Processor. Zrozumienie, skąd bierze się *sniffing*, to klucz do diagnozowania niestabilnych planów wykonania.

## Czym jest *parameter sniffing*?

Gdy zapytanie używa parametrów (np. w procedurze składowanej), SQL Server **pobiera wartość parametru podczas kompilacji planu wykonania**. Ta pierwsza wartość, którą „powącha” (sniff), zostaje użyta przez optymalizator do:

- oszacowania kardynalności,
- wyboru strategii wyszukiwania (index seek vs scan),
- wyboru join typów i kolejności,
- doboru operatorów (np. Nested Loops, Hash Match).

Plan powstały przy pierwszym wywołaniu trafia do **plan cache** i będzie używany dla kolejnych wywołań — nawet jeśli kolejne parametry są skrajnie inne.

## Kiedy *parameter sniffing* staje się problemem?

Mechanizm jest bardzo korzystny, o ile **rozkład danych jest równomierny**. Kłopoty zaczynają się wtedy, gdy mamy sytuację:

- pierwsze wykonanie: parametr jest „mały” (np. rzadki klient → tylko 15 wierszy),
- drugie wykonanie: parametr jest „duży” (np. klient hurtowy → 15 000 000 wierszy),

a SQL Server **nadal używa jednego wspólnego planu**.

W efekcie:

- plan zoptymalizowany pod mały zestaw danych może spowodować katastrofalny przebieg,  
- plan zoptymalizowany pod duży zestaw może być kompletnie nadmiarowy dla małego,  
- a obciążenie zmienia się dynamicznie w ciągu dnia.

## Co tak naprawdę powoduje *parameter sniffing*?

### ✅ **Główna przyczyna: różne wartości parametrów przy tych samych zapytaniach**

To **wartość parametru przekazana przy pierwszym wykonaniu** decyduje o tym, jaki plan trafi do cache. Jeśli dane są nierównomierne, kolejne wykonania mogą używać tego planu w nieoptymalnych warunkach.

**To nie indeksy, nie liczba danych i nie pamięć — tylko zmienność wartości parametrów**.

## Dlaczego SQL Server to robi?

Bo w większości przypadków to dobre podejście.

Sniffing pozwala Query Processor wybrać najbardziej optymalny plan dla konkretnej wartości parametru — zamiast generować „uśredniony” plan, który byłby wolniejszy dla wielu zapytań.

Kiedy jest dobrze:

- dane są równomierne,
- rozkład nie zmienia się drastycznie,
- parametry nie prowadzą do kardynalności o rzędy wielkości różne.

Kiedy jest źle:

- rozkład danych jest silnie „skośny” (skew),
- część wartości jest bardzo rzadka, część masowa,
- optymalizator „pomyli się” przez niepasujący plan.

## Jak diagnozować?

Charakterystyczne objawy:

- zapytanie raz działa w 50 ms, a raz w 20 sekund,
- zależy to od konkretnej wartości parametru,
- plany różnią się seek vs scan, joiny, wyborem operatorów,
- często w Actual Plan pojawia się gigantyczna różnica między „Estimated” a „Actual Rows”.

## Jak unikać złych skutków sniffingu?

Najczęstsze techniki:

- **OPTION (RECOMPILE)** — plan za każdym razem od nowa.  
- **OPTIMIZE FOR (@param = …)** — optymalizacja pod wybraną wartość.  
- **OPTIMIZE FOR UNKNOWN** — plan uśredniony z histogramu.  
- **Podział procedur** — rozdzielenie ścieżek „małych” i „dużych”.  
- **PSPO (SQL Server 2022)** — wiele planów dla jednego zapytania w zależności od wartości (Intelligent Query Processing).

---

## Demo T‑SQL
W skrócie: tworze bazę z rozkładem skośnym, procedurę z parametrem i pokazuje, jak zmienia się plan w zależności od pierwszej wartości.

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


---

## Podsumowanie

*Parameter sniffing* nie jest błędem — jest mechanizmem.  
Problem pojawia się tylko wtedy, gdy **różne wartości parametrów generują skrajnie różne rozkłady danych**.

**Dlatego prawidłowa odpowiedź w quizie brzmi:** *różne wartości parametru prowadzą do różnych planów przy współdzielonym planie w cache.*

Zrozumienie sniffingu to fundament pracy z Query Processor.
