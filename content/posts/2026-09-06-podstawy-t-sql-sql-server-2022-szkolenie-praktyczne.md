---
title: "Podstawy T-SQL w SQL Server 2022 — 5-dniowe szkolenie praktyczne"
date: "2026-09-06"
slug: "podstawy-t-sql-sql-server-2022-szkolenie-praktyczne"
draft: false
description: "Praktyczne 5-dniowe szkolenie z T-SQL na SQL Server 2022: AdventureWorks2022, 20 laboratoriów, demonstracje, zadania biznesowe i końcowy Capstone."
tags: ["SQL Server", "T-SQL", "Szkolenia", "SQL Server 2022", "AdventureWorks"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/podstawy-t-sql-sql-server-2022-szkolenie-praktyczne/"
---

SQL-a można uczyć jako listy poleceń. Można też uczyć go jako sposobu rozwiązywania problemów z danymi.

Właśnie z tego drugiego założenia powstało moje szkolenie **„Podstawy T-SQL w SQL Server 2022”** — pięć dni pracy od pierwszego `SELECT` aż do procedury składowanej z walidacją parametrów, obsługą błędów i raportem końcowym.

To nie jest oficjalny kurs Microsoft i nie przygotowuje do konkretnego egzaminu certyfikacyjnego. Program jest oparty na sprawdzonych fundamentach T-SQL, ale został zaktualizowany do **SQL Server 2022** i ułożony pod praktyczną pracę na danych.

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone dla osób, które chcą nauczyć się **świadomie czytać i pisać T-SQL**, między innymi:

- analityków pracujących z danymi,
- początkujących programistów,
- osób wchodzących w obszar DBA lub BI,
- administratorów, którzy chcą uporządkować fundamenty języka T-SQL,
- zespołów, które korzystają z SQL Server, ale chcą pisać bardziej przewidywalne i czytelne zapytania.

Nie jest wymagane wcześniejsze doświadczenie z T-SQL. Wystarczy rozumienie pojęć takich jak tabela, kolumna i wiersz.

## Jak wygląda praca podczas szkolenia?

Każdy blok ma podobny rytm:

1. krótkie omówienie mechanizmu,
2. demonstracja prowadzącego,
3. samodzielny lab uczestnika,
4. omówienie rozwiązania,
5. opcjonalny Bug Hunt albo challenge, jeśli pozwala czas.

W praktyce oznacza to około **40% omówienia i demonstracji oraz 60% pracy własnej**.

Demo i lab nie są kopiami tego samego zapytania. Demonstracja pokazuje mechanizm, natomiast uczestnik musi zastosować go później w innym scenariuszu.

## Jedno środowisko przez całe pięć dni

Szkolenie pracuje na jednym spójnym środowisku:

- **SQL Server 2022 Developer Edition**,
- Docker Desktop na Windows,
- SQL Server Management Studio lub Visual Studio Code z rozszerzeniem MSSQL,
- baza **AdventureWorks2022**,
- compatibility level 160,
- dodatkowy schemat `Training` dla ćwiczeń modyfikujących dane.

AdventureWorks2022 jest odtwarzana automatycznie z oficjalnego backupu Microsoftu. Dzięki temu uczestnicy pracują na tym samym modelu danych, a ćwiczenia można powtarzać bez ręcznego przygotowywania środowiska.

## Nie „Zadanie 3”, tylko problem do rozwiązania

Chciałem uniknąć sytuacji, w której uczestnik przez pięć dni wykonuje oderwane od siebie ćwiczenia.

Dlatego szkolenie ma prostą historię biznesową. Zadania przychodzą od trzech osób:

- **Anna z IT** pilnuje jakości, procedur i poprawności wykonania,
- **Piotr ze sprzedaży** potrzebuje rankingów, analiz i danych do dalszego wykorzystania,
- **Maria z marketingu** pracuje z produktami, kategoriami i zachowaniami klientów.

Zamiast samego „napisz zapytanie z `EXISTS`” uczestnik dostaje pytanie biznesowe, na które trzeba odpowiedzieć za pomocą SQL-a.

## Program — 5 dni

### Dzień 1 — fundamenty i pobieranie danych

Zaczynamy od środowiska, struktury bazy i podstaw języka:

- baza, schemat, tabela,
- logiczna kolejność wykonywania zapytania,
- `SELECT`, aliasy, `DISTINCT`, `CASE`,
- `NULL` i logika trójwartościowa,
- `INNER JOIN`, `LEFT JOIN`, `CROSS JOIN`, self join,
- różnica między warunkiem w `ON` i `WHERE`.

Już pierwszego dnia uczestnik buduje zapytania na rzeczywistym modelu relacyjnym AdventureWorks.

### Dzień 2 — filtrowanie, typy danych i DML

Drugi dzień to przejście od odczytu do bezpiecznej pracy z danymi:

- `ORDER BY`, `TOP`, `OFFSET/FETCH`, `IN`, `LIKE`, `BETWEEN`,
- poprawne filtrowanie zakresów dat,
- `CAST`, `CONVERT`, `TRY_CAST`, `TRY_CONVERT`,
- `DATEADD`, `DATEDIFF`, `EOMONTH`, `DATETRUNC`,
- `INSERT`, `UPDATE`, `DELETE`, `OUTPUT`, `MERGE`, `SELECT INTO`, `TRUNCATE`,
- `COALESCE`, `ISNULL`, `NULLIF`, `GREATEST`, `LEAST`,
- `STRING_SPLIT` z ordinal,
- `IS [NOT] DISTINCT FROM`.

Operacje DML trafiają do osobnego schematu `Training`, więc można ćwiczyć bez naruszania danych referencyjnych AdventureWorks.

### Dzień 3 — raportowanie i wyrażenia tabelaryczne

Tutaj zapytania zaczynają przypominać prawdziwe raporty:

- `GROUP BY`, `HAVING`, agregaty,
- `DATE_BUCKET`,
- podzapytania skalarne i wielowierszowe,
- `EXISTS` i podzapytania skorelowane,
- derived tables,
- widoki i inline TVF,
- CTE i CTE rekurencyjne,
- `UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`,
- `CROSS APPLY`, `OUTER APPLY`,
- `GENERATE_SERIES`.

### Dzień 4 — analiza danych, procedury i JSON

Czwarty dzień to funkcje analityczne i przygotowanie kodu do wielokrotnego użycia:

- `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`,
- `LAG`, `LEAD`, running total i ramy okna,
- klauzula `WINDOW`,
- `PIVOT`, `UNPIVOT`, `GROUPING SETS`, `ROLLUP`, `CUBE`,
- procedury składowane i parametry,
- `FOR JSON PATH` i `FOR JSON AUTO`,
- `JSON_VALUE`, `JSON_QUERY`,
- `JSON_OBJECT`, `JSON_ARRAY`, `JSON_PATH_EXISTS`.

### Dzień 5 — programowanie, błędy, transakcje i Capstone

Ostatni dzień łączy język z bezpiecznym wykonaniem kodu:

- zmienne, `IF...ELSE`, `WHILE`,
- dynamiczny SQL przez `sp_executesql`,
- `TRY...CATCH`, funkcje `ERROR_*`, `THROW`,
- transakcje jawne,
- `@@TRANCOUNT`, `XACT_STATE()`, `XACT_ABORT`,
- podstawy izolacji i dirty read,
- końcowy **Lab 20 — Capstone**.

## Capstone — pięć dni w jednym zadaniu

Finałowy lab nie wprowadza nowej składni. Jego celem jest złożenie poznanych mechanizmów w jedną historię.

Uczestnik buduje rozwiązanie, które między innymi:

- określa, czy klient kupił produkt z kategorii Bikes (`EXISTS`),
- agreguje sprzedaż za rok raportowy,
- tworzy ranking klientów w obrębie terytorium (`RANK`),
- zamyka logikę w procedurze z parametrami,
- waliduje rok i zgłasza błąd przez `THROW`,
- zapisuje informacje o błędzie,
- generuje wynik jako JSON.

To moment, w którym wcześniejsze JOIN-y, CTE, podzapytania, funkcje okienkowe i procedury przestają być osobnymi tematami.

## 20 laboratoriów + zadania dodatkowe

Pełny materiał obejmuje:

- **20 laboratoriów** w wariantach Starter i Solution,
- demonstracje dla prowadzącego,
- challenge'e na zakończenie dni,
- Bug Hunt — celowo zepsute skrypty do diagnozy,
- materiały dla uczestnika: mapa bazy i ściągawka,
- pretest i posttest,
- scenariusz oraz notatki dla trenera.

## Czego to szkolenie nie obejmuje?

Zakres świadomie dotyczy języka T-SQL. Nie jest to szkolenie z administracji SQL Server.

Nie wchodzimy więc w szczegóły:

- backup/recovery,
- Always On i FCI,
- administracji bezpieczeństwem,
- Query Store i zaawansowanego tuningu,
- przygotowania do egzaminu Microsoft.

Dzięki temu przez pięć dni możemy skupić się na jednej rzeczy: **dobrym rozumieniu T-SQL**.

## Forma organizacyjna

Szkolenie trwa **5 dni, 09:00–16:00** i najlepiej sprawdza się jako szkolenie zamknięte dla zespołu do około 12 osób.

Może być prowadzone stacjonarnie lub online, po wcześniejszym uzgodnieniu środowiska uczestników.

Jeżeli interesuje Cię szkolenie dla zespołu, pełny opis usługi znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać grupę, jej poziom oraz oczekiwany rezultat szkolenia.
