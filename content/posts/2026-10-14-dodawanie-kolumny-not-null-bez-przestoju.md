---
title: "NOT NULL bez przestoju: jak bezpiecznie dodać obowiązkową kolumnę"
date: 2026-10-14T00:01:00+02:00
slug: "not-null-bez-przestoju"
description: "Bezpieczny wzorzec dodawania obowiązkowej kolumny do dużej tabeli bez jednego ryzykownego wdrożenia."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - schema evolution
  - NOT NULL
  - zero downtime
  - database DevOps
draft: false
---

# NOT NULL bez przestoju: jak bezpiecznie dodać obowiązkową kolumnę

Pozornie prosta zmiana:

```sql
ALTER TABLE dbo.Orders
ADD SourceSystem varchar(20) NOT NULL;
```

na dużej tabeli może być wszystkim, tylko nie prostą zmianą.

Bezpieczniej rozbić ją na kilka etapów.

## Etap 1 — kolumna nullable

```sql
ALTER TABLE dbo.Orders
ADD SourceSystem varchar(20) NULL;
```

Stary kod nadal działa, bo nie musi jeszcze znać nowej kolumny.

## Etap 2 — nowy kod zapisuje wartość

Od tego momentu wszystkie nowe rekordy powinny mieć `SourceSystem`.

Można monitorować naruszenia:

```sql
SELECT COUNT(*) AS MissingValueCount
FROM dbo.Orders
WHERE SourceSystem IS NULL;
```

## Etap 3 — backfill

Uzupełniamy stare dane partiami.

```sql
WHILE 1 = 1
BEGIN
    UPDATE TOP (10000) dbo.Orders
    SET SourceSystem = 'LEGACY'
    WHERE SourceSystem IS NULL;

    IF @@ROWCOUNT = 0 BREAK;

    WAITFOR DELAY '00:00:00.200';
END;
```

Rozmiar partii powinien wynikać z obserwacji logu, blokad i czasu wykonania.

## Etap 4 — walidacja

```sql
SELECT COUNT(*)
FROM dbo.Orders
WHERE SourceSystem IS NULL;
```

Zero to dopiero początek. Trzeba jeszcze potwierdzić, że wszystkie aktywne wersje aplikacji zapisują wartość.

## Etap 5 — NOT NULL

```sql
ALTER TABLE dbo.Orders
ALTER COLUMN SourceSystem varchar(20) NOT NULL;
```

To powinien być osobny krok wdrożenia.

## A co z DEFAULT?

Default może pomóc dla nowych rekordów:

```sql
ALTER TABLE dbo.Orders
ADD CONSTRAINT DF_Orders_SourceSystem
DEFAULT ('APP') FOR SourceSystem;
```

Nie powinien jednak maskować błędu aplikacji bez świadomej decyzji.

## Najważniejsza zasada

Najpierw spraw, żeby ograniczenie było **prawdą biznesową i faktyczną**, a dopiero później wymuś je technicznie.

## Podsumowanie

Zmiana `NULL -> NOT NULL` nie musi być jednym poleceniem.

Expand, zapis nowej wartości, backfill, walidacja i dopiero constraint — to dużo spokojniejsza droga.