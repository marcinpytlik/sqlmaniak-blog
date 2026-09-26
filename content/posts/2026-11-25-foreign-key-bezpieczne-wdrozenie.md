---
title: "Foreign Key bez niespodzianki: jak bezpiecznie wdrożyć relację na istniejących danych"
date: 2026-11-25T00:01:00+01:00
slug: "foreign-key-bezpieczne-wdrozenie"
description: "Jak dodać klucz obcy do istniejącego modelu danych, najpierw wykrywając sieroty i dopiero potem wymuszając integralność."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - foreign key
  - schema evolution
  - data quality
  - database DevOps
draft: false
---

# Foreign Key bez niespodzianki: jak bezpiecznie wdrożyć relację na istniejących danych

Dodanie Foreign Key do pustej tabeli jest proste.

Na istniejącym systemie trzeba najpierw sprawdzić, czy dane już spełniają nową regułę.

## Znajdź sieroty

```sql
SELECT c.CustomerId
FROM dbo.Orders AS c
LEFT JOIN dbo.Customers AS p
    ON p.CustomerId = c.CustomerId
WHERE p.CustomerId IS NULL;
```

Jeżeli wynik nie jest pusty, constraint nie naprawi danych za nas.

## Najpierw dane

Trzeba ustalić, co oznaczają rekordy osierocone:

- błąd historyczny,
- usunięte dane nadrzędne,
- brakujący backfill,
- dozwolony przypadek biznesowy.

## Dodanie constraintu

```sql
ALTER TABLE dbo.Orders WITH CHECK
ADD CONSTRAINT FK_Orders_Customers
FOREIGN KEY (CustomerId)
REFERENCES dbo.Customers(CustomerId);
```

`WITH CHECK` powoduje weryfikację istniejących danych.

## Untrusted constraint

Constraint dodany z `WITH NOCHECK` może istnieć, ale nie być zaufany przez silnik.

Sprawdź:

```sql
SELECT
    name,
    is_disabled,
    is_not_trusted
FROM sys.foreign_keys
WHERE parent_object_id = OBJECT_ID(N'dbo.Orders');
```

## Walidacja później

Jeżeli migracja wymaga etapu przejściowego, można najpierw uporządkować dane, a potem wykonać:

```sql
ALTER TABLE dbo.Orders WITH CHECK
CHECK CONSTRAINT FK_Orders_Customers;
```

## Wydajność

Kolumna po stronie child zwykle powinna mieć odpowiedni indeks, szczególnie przy częstych joinach i usuwaniu rekordów nadrzędnych.

## Podsumowanie

Foreign Key nie jest tylko deklaracją modelu. Jest dowodem, że istniejące dane spełniają relację.

Najpierw jakość danych, potem wymuszenie.