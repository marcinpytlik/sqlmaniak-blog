---
title: "EF Core Through the Eyes of a DBA — 3-dniowe szkolenie praktyczne"
date: "2026-10-02"
slug: "ef-core-through-the-eyes-of-a-dba-szkolenie-praktyczne"
draft: false
description: "Praktyczne 3-dniowe szkolenie pokazujące, jak decyzje w C# i Entity Framework Core zamieniają się w rzeczywisty workload SQL Servera: generated SQL, execution plans, indeksy, blocking, deadlocki, Query Store i N+1."
tags: ["SQL Server", "Entity Framework Core", "EF Core", ".NET", "Performance", "Query Store", "Szkolenia"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/ef-core-through-the-eyes-of-a-dba-szkolenie-praktyczne/"
---

Kod aplikacji może wyglądać poprawnie.

Endpoint może zwracać właściwe dane.

A mimo to SQL Server może dostawać zapytania, które pobierają za dużo danych, wykonują zbyt wiele round-tripów, źle wykorzystują indeksy albo trzymają transakcje dłużej, niż zakładaliśmy.

Właśnie z tego założenia powstało szkolenie **„EF Core Through the Eyes of a DBA — What Really Reaches SQL Server?”**.

To trzy dni praktycznej pracy na styku dwóch perspektyw:

- developera .NET, który widzi C#, LINQ, encje i endpointy,
- DBA, który widzi SQL, plany wykonania, logical reads, locks, waits i Query Store.

Główne pytanie szkolenia brzmi:

> **What really reaches SQL Server?**

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone przede wszystkim dla:

- developerów .NET pracujących z Entity Framework Core i SQL Server,
- administratorów SQL Server współpracujących z zespołami developerskimi,
- architektów aplikacji i baz danych,
- zespołów Dev + DBA, które chcą wspólnie diagnozować problemy wydajnościowe,
- osób, które potrafią pisać LINQ, ale chcą lepiej rozumieć wygenerowany SQL,
- osób, które analizują SQL Server, ale chcą zobaczyć, jakie decyzje po stronie aplikacji prowadzą do konkretnego workloadu.

Uczestnik powinien znać podstawy C#, LINQ i relacyjnych baz danych.

Nie jest wymagana zaawansowana wiedza z performance tuningu SQL Servera.

## Jak wygląda praca podczas szkolenia?

Pracujemy na jednym spójnym środowisku:

- ASP.NET Core Web API,
- Entity Framework Core,
- SQL Server,
- jedna przygotowana baza,
- te same endpointy i dane przez wszystkie trzy dni.

Każdy blok ma podobny rytm:

1. problem widoczny z perspektywy aplikacji,
2. wygenerowanie workloadu,
3. zebranie evidence po stronie SQL Servera,
4. interpretacja planu, reads, waits lub Query Store,
5. przejście do kodu C#,
6. wskazanie przyczyny,
7. poprawka,
8. ponowna walidacja.

Nie zaczynamy od zgadywania.

Zaczynamy od dowodów.

## Format — 3 dni

Szkolenie trwa **3 dni** i jest zaprojektowane jako praktyczna praca z kodem, SQL Serverem i diagnostyką.

Materiał opiera się na **12 laboratoriach** połączonych w jeden spójny scenariusz.

### Dzień 1 — From HTTP Request to SQL Server

Pierwszy dzień buduje najważniejszy model mentalny: jak decyzja w kodzie aplikacji zamienia się w SQL.

Zakres:

- HTTP request → ASP.NET Core → EF Core → SQL Server,
- DbContext, DbSet i IQueryable,
- deferred execution,
- moment materializacji,
- ToListAsync() i FirstAsync(),
- logowanie Microsoft.EntityFrameworkCore.Database.Command,
- parametryzacja,
- analiza wygenerowanego SQL,
- Include() i kształt result setu,
- Take() przed LEFT JOIN,
- dlaczego wynik SQL może mieć więcej wierszy niż liczba encji,
- projection vs pełne encje,
- over-fetching,
- payload HTTP,
- materializacja obiektów,
- wprowadzenie do problemu N+1.

Najważniejsze pytania dnia:

- co SQL Server naprawdę dostaje z EF Core,
- gdzie kończy się LINQ, a zaczyna SQL,
- kiedy kod funkcjonalnie poprawny generuje zbyt szeroki workload,
- kiedy Include() ma sens, a kiedy lepsza jest projection.

### Dzień 2 — Execution Plans, Indexes and Concurrency

Drugiego dnia przechodzimy od samego SQL do sposobu jego wykonania.

Zakres:

- Actual Execution Plan,
- Scan vs Seek,
- estimated rows vs actual rows,
- logical reads,
- indeksy i ich wpływ na plan,
- Key Lookup,
- covering index,
- SARGability,
- funkcje na indeksowanych kolumnach,
- ten sam wynik funkcjonalny, inny koszt wykonania,
- transaction lifetime,
- locking,
- blocking,
- blocking_session_id,
- LCK_M_*,
- sys.dm_exec_requests,
- sys.dm_tran_locks,
- READ COMMITTED,
- READ UNCOMMITTED,
- dirty read,
- deadlock,
- deadlock victim,
- error 1205,
- deadlock graph i system_health.

Najważniejszy cel dnia:

> Nie traktować Scan, Seek, blocking ani deadlocka jako etykiety — tylko jako evidence, które trzeba osadzić w kontekście aplikacji.

### Dzień 3 — Query Store and Real Workload Diagnosis

Trzeci dzień łączy wszystko w pełną analizę incydentu.

Zakres:

- Query Store,
- identyfikacja workloadu po query_sql_text,
- execution count,
- duration,
- CPU,
- logical reads,
- szeroki graph query,
- problem N+1,
- jeden kosztowny statement vs wiele tanich statementów,
- powiązanie SQL z endpointem,
- przejście od evidence do kodu,
- Application / Database / Both,
- Impact / Effort,
- poprawka i walidacja,
- pełny przepływ diagnostyczny:

**Symptom → Evidence → Root cause → Fix → Validation**

Finałem jest analiza kilku wariantów tego samego problemu:

- **BAD** — za dużo w jednym zapytaniu,
- **N+1** — za dużo zapytań,
- **GOOD** — workload dopasowany do rzeczywistej potrzeby API.

## 12 laboratoriów

Szkolenie wykorzystuje 12 laboratoriów, które prowadzą uczestnika od prostego requestu do pełnej analizy workloadu.

Obszary laboratoriów obejmują między innymi:

- generated SQL,
- deferred execution,
- projection i over-fetching,
- plany wykonania,
- indeksy,
- SARGability,
- blocking,
- isolation levels,
- deadlock,
- Query Store,
- N+1,
- końcową analizę problemu aplikacyjno-bazodanowego.

Laboratoria są zaprojektowane tak, aby uczestnik nie tylko zobaczył wynik, ale potrafił odpowiedzieć:

- co dokładnie się wydarzyło,
- jaki evidence to potwierdza,
- gdzie znajduje się root cause,
- czy poprawka powinna być po stronie aplikacji, bazy czy obu warstw,
- jak zweryfikować efekt zmiany.

## Czego uczestnik nauczy się po szkoleniu?

Po szkoleniu uczestnik potrafi:

- znaleźć SQL generowany przez EF Core,
- wyjaśnić, dlaczego SQL ma konkretny kształt,
- rozpoznać deferred execution i moment materializacji,
- ocenić wpływ Include() i projection na workload,
- analizować Scan, Seek i Key Lookup w kontekście rzeczywistego zapytania,
- porównywać logical reads zamiast opierać się tylko na czasie wykonania,
- rozpoznać problem SARGability,
- diagnozować blocking i wskazać blocker,
- odróżnić blocking od deadlocka,
- odczytać podstawowe informacje z deadlock graph,
- wykorzystać Query Store do identyfikacji workloadu,
- rozpoznać szeroki graph query i N+1,
- zdecydować, czy poprawka należy do warstwy aplikacji, bazy czy obu,
- walidować zmianę na podstawie pomiarów.

## To nie jest kurs „EF Core jest zły”

Celem szkolenia nie jest przekonywanie, że ORM jest dobry albo zły.

Entity Framework Core jest narzędziem.

Problem zaczyna się wtedy, gdy zespół widzi tylko kod C# albo tylko SQL Server i nie potrafi połączyć obu perspektyw.

Dlatego jednym z najważniejszych zdań szkolenia jest:

> **The application generates the workload. SQL Server executes the workload it receives.**

## Materiały szkoleniowe

Uczestnicy pracują na przygotowanym środowisku oraz materiałach obejmujących:

- aplikację ASP.NET Core,
- bazę SQL Server,
- instrukcje uruchomienia środowiska,
- laboratoria,
- skrypty diagnostyczne,
- przykłady generated SQL,
- Query Store,
- scenariusze blocking i deadlock,
- checklisty i materiały do samodzielnego powtórzenia ćwiczeń po szkoleniu.

## Forma organizacyjna

Szkolenie trwa **3 dni**.

Najlepiej sprawdza się jako zamknięte szkolenie dla zespołów .NET + SQL Server, w których problemy wydajnościowe wymagają współpracy developerów i DBA.

Może być prowadzone stacjonarnie lub online, po wcześniejszym uzgodnieniu środowiska i poziomu uczestników.

Pełny opis usług znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać technologię, poziom zespołu oraz oczekiwany rezultat szkolenia.
