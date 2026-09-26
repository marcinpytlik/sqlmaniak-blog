---
title: "INT do BIGINT: jak migrować klucz główny bez jednego wielkiego ALTER"
date: 2026-11-18T00:01:00+01:00
slug: "migracja-klucza-glownego-int-do-bigint"
description: "Jak przygotować migrację klucza głównego z int do bigint w dużym systemie, uwzględniając klucze obce, indeksy i aplikację."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - schema evolution
  - BIGINT
  - primary key
  - migracja danych
draft: false
---

# INT do BIGINT: jak migrować klucz główny bez jednego wielkiego ALTER

Przejście z `int` do `bigint` dla klucza głównego brzmi jak zmiana typu danych.

W praktyce jest zmianą całego grafu zależności.

## Najpierw policz zakres

```sql
SELECT
    MAX(Id) AS MaxId,
    CAST(MAX(Id) AS decimal(19,0)) * 100.0 / 2147483647 AS IntUsagePercent
FROM dbo.Orders;
```

Nie czekaj, aż zabraknie wartości.

## Dlaczego proste ALTER jest ryzykowne?

Klucz główny może być:

- referencją dla wielu kluczy obcych,
- częścią indeksów,
- używany w tabelach historii,
- przesyłany przez API,
- mapowany w ORM jako `int`.

## Nowy klucz obok starego

```sql
ALTER TABLE dbo.Orders
ADD OrderIdBigint bigint NULL;
```

Potem wykonujemy backfill i budujemy nowy indeks.

## Klucze obce

Każda tabela zależna również potrzebuje nowej kolumny:

```sql
ALTER TABLE dbo.OrderLines
ADD OrderIdBigint bigint NULL;
```

Do migracji przydaje się jednoznaczna mapa `OldId -> NewId`, zwłaszcza gdy nowy identyfikator nie jest prostym rzutowaniem.

## Aplikacja

Model aplikacyjny musi przez okres przejściowy rozumieć oba klucze.

To dobry moment na:

- nowy kontrakt API,
- shadow read,
- telemetrykę porównawczą,
- stopniowe przełączanie modułów.

## Contract dopiero na końcu

Stary `int` można usunąć dopiero po migracji wszystkich referencji.

## Podsumowanie

Migracja klucza głównego to nie `ALTER COLUMN`. To projekt zmiany kontraktu pomiędzy tabelami i aplikacjami.