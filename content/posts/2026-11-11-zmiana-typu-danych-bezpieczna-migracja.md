---
title: "Zmiana typu danych bez blokady: nowa kolumna zamiast ALTER COLUMN"
date: 2026-11-11T00:01:00+01:00
slug: "zmiana-typu-danych-bezpieczna-migracja"
description: "Jak zmieniać typ danych w dużej tabeli etapami, zamiast wykonywać ryzykowne ALTER COLUMN na żywym systemie."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - schema evolution
  - data type
  - zero downtime
  - database DevOps
draft: false
---

# Zmiana typu danych bez blokady: nowa kolumna zamiast ALTER COLUMN

`ALTER COLUMN` wygląda niewinnie, dopóki tabela nie ma setek milionów rekordów.

Zmiana typu może wymagać przebudowy danych, indeksów i zależności.

## Przykład

Chcemy przejść z:

```text
OrderNumber varchar(20)
```

na:

```text
OrderNumber bigint
```

## Etap 1 — nowa kolumna

```sql
ALTER TABLE dbo.Orders
ADD OrderNumberBigint bigint NULL;
```

## Etap 2 — walidacja konwersji

```sql
SELECT OrderNumber
FROM dbo.Orders
WHERE TRY_CONVERT(bigint, OrderNumber) IS NULL
  AND OrderNumber IS NOT NULL;
```

Najpierw poznaj rekordy, których nie da się przenieść.

## Etap 3 — backfill partiami

```sql
UPDATE TOP (10000) dbo.Orders
SET OrderNumberBigint = TRY_CONVERT(bigint, OrderNumber)
WHERE OrderNumberBigint IS NULL
  AND OrderNumber IS NOT NULL;
```

## Etap 4 — dual-write

Nowa wersja aplikacji zapisuje obie reprezentacje albo jedną i synchronizuje drugą.

## Etap 5 — przełącz odczyt

Po walidacji nowa kolumna staje się źródłem odczytu.

## Indeksy

Nie zapominaj, że indeksy zależne od starej kolumny trzeba zaplanować osobno.

Możesz przygotować nowy indeks jeszcze przed przełączeniem:

```sql
CREATE INDEX IX_Orders_OrderNumberBigint
ON dbo.Orders(OrderNumberBigint);
```

## Contract

Stara kolumna znika dopiero wtedy, gdy:

- wszystkie odczyty używają nowej,
- wszystkie zapisy używają nowej,
- integracje zostały przełączone,
- dane są zweryfikowane,
- rollback nie wymaga starej reprezentacji.

## Podsumowanie

Zmiana typu danych nie musi być jedną operacją DDL.

Nowa kolumna, backfill, walidacja i przełączenie dają znacznie większą kontrolę nad ryzykiem.