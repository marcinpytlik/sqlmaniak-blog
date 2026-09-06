---
title: "Zaawansowany T-SQL i rozwój baz danych w SQL Server 2022 — 5-dniowe szkolenie praktyczne"
date: "2026-09-07"
slug: "zaawansowany-t-sql-sql-server-2022-szkolenie-praktyczne"
draft: false
description: "Praktyczne 5-dniowe szkolenie z zaawansowanego T-SQL i rozwoju baz danych w SQL Server 2022: indeksy, Query Store, PSP, temporal, columnstore, procedury, UDF, In-Memory OLTP, XML, JSON, Spatial, Full-Text, współbieżność i Capstone."
tags: ["SQL Server", "T-SQL", "Szkolenia", "SQL Server 2022", "Performance", "AdventureWorks"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/zaawansowany-t-sql-sql-server-2022-szkolenie-praktyczne/"
---

Znajomość składni T-SQL to jedno. Świadome projektowanie tabel, indeksów, procedur i rozwiązań, które mają działać przewidywalnie pod obciążeniem — to już kolejny poziom.

Właśnie temu poświęcone jest moje szkolenie **„Zaawansowany T-SQL i rozwój baz danych w SQL Server 2022”**. Przez pięć dni przechodzimy od projektowania struktur danych i strategii indeksowych, przez programowalność po stronie bazy, aż do współbieżności, Query Store i końcowego Capstone.

To nie jest oficjalny kurs Microsoft i nie przygotowuje do konkretnego egzaminu certyfikacyjnego. Program zachowuje logiczne fundamenty dawnego kursu **20762C Developing SQL Databases**, ale został przeprojektowany pod **SQL Server 2022**, współczesne mechanizmy silnika i praktyczną pracę z bazą danych.

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone dla osób, które znają już podstawy T-SQL i chcą wejść głębiej w rozwój baz danych SQL Server, między innymi dla:

- programistów pracujących z SQL Server,
- administratorów DBA, którzy chcą lepiej rozumieć kod aplikacyjny i jego wpływ na silnik,
- developerów baz danych,
- architektów i osób odpowiedzialnych za model danych,
- zespołów utrzymujących rozwiązania, w których wydajność i współbieżność mają realne znaczenie.

Uczestnik powinien swobodnie posługiwać się `SELECT`, `JOIN`, agregacjami, CTE, podstawowym DML oraz rozumieć, czym są procedury i transakcje.

## Jak wygląda praca podczas szkolenia?

Każdy blok ma stały rytm:

1. krótkie omówienie mechanizmu,
2. demonstracja prowadzącego,
3. samodzielny lab uczestnika,
4. analiza wyniku, planu wykonania albo zachowania silnika,
5. challenge lub dodatkowe demo, jeśli pozwala czas.

W praktyce oznacza to około **40% omówienia i demonstracji oraz 60% pracy własnej**.

W tym szkoleniu szczególnie ważne jest jedno: nie interesuje nas tylko to, czy zapytanie „zwraca poprawny wynik”. Patrzymy również na to, **jak SQL Server je wykonuje, jakie przyjmuje założenia i co stanie się z rozwiązaniem przy innym rozkładzie danych lub większej konkurencji**.

## Środowisko przygotowane pod cały kurs

Szkolenie pracuje na jednym spójnym środowisku:

- **SQL Server 2022 Developer Edition**,
- Docker Desktop na Windows,
- własny obraz szkoleniowy z Full-Text Search,
- SQL Server Management Studio lub Visual Studio Code z rozszerzeniem MSSQL,
- baza **AdventureWorks2022**,
- dodatkowy schemat `TrainingAdvanced`,
- compatibility level 160,
- Query Store,
- `ALLOW_SNAPSHOT_ISOLATION`,
- dane przygotowane pod demonstracje selektywności, planów i Parameter Sensitive Plan optimization.

Środowisko można odtworzyć automatycznie. Są też resety poszczególnych dni, dzięki czemu ćwiczenia można powtarzać bez ponownego budowania całej bazy.

## Program — 5 dni

### Dzień 1 — projektowanie struktur danych

Pierwszy dzień dotyczy fundamentów, ale już z perspektywy developera bazy danych:

- lifecycle obiektu bazodanowego,
- schematy i kontrakty danych,
- dobór typów danych,
- `IDENTITY`, `SEQUENCE`, wartości domyślne i computed columns,
- temporal tables,
- kompresja row/page,
- partycjonowanie jako decyzja architektoniczna i operacyjna,
- `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `CHECK`,
- trusted i untrusted constraints.

Opcjonalnie, jeśli czas pozwala, pokazuję również **Ledger w SQL Server 2022** — wraz z jasnym rozróżnieniem, czym Ledger jest, a czym nie jest.

### Dzień 2 — indeksy i warstwa dostępu

Drugi dzień koncentruje się na świadomym projektowaniu dostępu do danych:

- heap vs clustered index,
- nonclustered indexes,
- key lookup,
- selektywność i SARGability,
- indeksy pokrywające i filtrowane,
- statystyki i plany wykonania,
- Query Store,
- kontekst Parameter Sensitive Plan optimization,
- clustered i nonclustered columnstore,
- rowgroups i segment elimination,
- widoki, `SCHEMABINDING` i indexed views.

Nie kończymy na samym `CREATE INDEX`. Patrzymy, czy indeks faktycznie zmienia sposób wykonania zapytania i jaki koszt powoduje po stronie DML.

### Dzień 3 — programowalność po stronie bazy

Trzeci dzień to procedury, funkcje i kod wykonywany po stronie SQL Server:

- procedury składowane i parametry,
- `CREATE OR ALTER`,
- `EXECUTE AS`,
- plan cache i parameter sniffing,
- **Parameter Sensitive Plan optimization w SQL Server 2022**,
- scalar UDF, inline TVF i multi-statement TVF,
- scalar UDF inlining,
- triggery i poprawna obsługa operacji wielowierszowych,
- `inserted` i `deleted`,
- In-Memory OLTP,
- memory-optimized tables,
- `SCHEMA_ONLY` vs `SCHEMA_AND_DATA`,
- natively compiled procedures.

PSP pokazujemy na rzeczywiście skośnym zestawie danych, tak aby różnica pomiędzy częstym i rzadkim parametrem była widoczna, a nie tylko opowiedziana na slajdzie.

### Dzień 4 — XML, Spatial, Full-Text i JSON

Czwarty dzień łączy mechanizmy specjalistyczne z integracją danych:

- CLR jako decyzja architektoniczna — kiedy T-SQL przestaje być właściwym narzędziem,
- typ `xml`, `FOR XML`, `value`, `query`, `nodes`, `exist`,
- `geometry` i `geography`,
- odległości i wyszukiwanie lokalizacji,
- `varbinary(max)` i przechowywanie dokumentów,
- Full-Text Search i `CONTAINS`,
- `ISJSON`, `JSON_VALUE`, `JSON_QUERY`, `OPENJSON`,
- `FOR JSON PATH`,
- `JSON_OBJECT`, `JSON_ARRAY`, `JSON_PATH_EXISTS`.

Spatial pracuje na zestawie lokalizacji w Polsce, a JSON jest traktowany jako realny kontrakt integracyjny, nie tylko sposób na sformatowanie wyniku.

### Dzień 5 — współbieżność, wydajność i Capstone

Ostatni dzień spina punkt widzenia developera z zachowaniem silnika:

- locks, blocking i deadlocki,
- poziomy izolacji,
- READ COMMITTED vs SNAPSHOT,
- RCSI jako decyzja na poziomie bazy,
- dlaczego `NOLOCK` nie jest rozwiązaniem problemów współbieżności,
- plany rzeczywiste,
- DMVs,
- wait statistics,
- Query Store,
- Query Store hints,
- analiza regresji według schematu: hipoteza → pomiar → zmiana → ponowny pomiar.

Popołudnie zajmuje **Lab 20 — Capstone**.

## Capstone — Customer 360

Końcowe zadanie łączy kilka obszarów szkolenia w jedno rozwiązanie.

Uczestnik buduje między innymi:

- filtrowany indeks wspierający konkretny workload,
- inline TVF z agregacją danych klienta,
- procedurę raportową z walidacją i obsługą błędów,
- wyszukiwanie najbliższej lokalizacji przez `geography`,
- wynik JSON zagnieżdżający dane kampanii i punktu sprzedaży,
- pomiar przez `STATISTICS IO`,
- weryfikację zachowania zapytań w Query Store.

Nie chodzi o wykorzystanie każdej możliwej funkcji SQL Server. Chodzi o świadome połączenie mechanizmów w rozwiązanie, które można później analizować i rozwijać.

## 20 laboratoriów i materiały dla trenera

Pełny materiał obejmuje:

- **20 laboratoriów** w wariantach Starter i Solution,
- demonstracje dla każdego modułu,
- challenge'e i Bug Hunt,
- dodatkowe demonstracje SQL Server 2022,
- pretest i posttest,
- ściągawkę oraz mapę obiektów dla uczestnika,
- scenariusze poszczególnych dni,
- oczekiwane wyniki kluczowych demonstracji wydajnościowych,
- reset środowiska per dzień.

Dzięki temu szkolenie można prowadzić jako spójny pięciodniowy warsztat, ale również wracać do pojedynczych obszarów podczas późniejszych ćwiczeń.

## Czego to szkolenie świadomie nie robi?

To nadal szkolenie z **rozwoju baz danych i zaawansowanego T-SQL**, a nie pełny kurs administracji SQL Server.

Nie zastępuje więc osobnych warsztatów z:

- backup/recovery i disaster recovery,
- Always On i FCI,
- hardeningu i administracji bezpieczeństwem,
- pełnego performance tuningu całej instancji,
- administracji systemem operacyjnym i storage.

Wydajność, Query Store i współbieżność pojawiają się tutaj dlatego, że developer bazy danych powinien rozumieć konsekwencje własnego kodu.

## Forma organizacyjna

Szkolenie trwa **5 dni, 09:00–16:00** i najlepiej sprawdza się jako szkolenie zamknięte dla zespołu do około 12 osób.

Może być prowadzone stacjonarnie lub online, po wcześniejszym uzgodnieniu środowiska uczestników.

Jeżeli zespół potrzebuje najpierw uporządkować fundamenty języka, dostępne jest również szkolenie **[Podstawy T-SQL w SQL Server 2022](/posts/podstawy-t-sql-sql-server-2022-szkolenie-praktyczne/)**.

Pełny opis usług znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać grupę, jej poziom oraz oczekiwany rezultat szkolenia.
