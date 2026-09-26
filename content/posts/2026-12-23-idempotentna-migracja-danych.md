---
title: "Idempotentna migracja danych: skrypt, który można uruchomić drugi raz"
date: 2026-12-23T00:01:00+01:00
slug: "idempotentna-migracja-danych"
description: "Jak projektować migracje danych tak, aby można było je bezpiecznie wznawiać po błędzie, restarcie lub przerwaniu procesu."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - idempotency
  - migracja danych
  - schema evolution
  - database DevOps
draft: false
---

# Idempotentna migracja danych: skrypt, który można uruchomić drugi raz

Długa migracja wcześniej czy później zostanie przerwana.

Sieć, failover, timeout, restart procesu — powód jest mniej ważny niż odpowiedź na pytanie:

> Czy mogę uruchomić proces jeszcze raz?

## Zły wariant

```sql
INSERT dbo.CustomerAddress (...)
SELECT ...
FROM dbo.Customer;
```

Drugie uruchomienie może utworzyć duplikaty.

## Idempotentny wariant

```sql
INSERT dbo.CustomerAddress
(
    CustomerId, AddressType, AddressLine1
)
SELECT
    c.CustomerId, 'PRIMARY', c.AddressLine1
FROM dbo.Customer AS c
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.CustomerAddress AS a
    WHERE a.CustomerId = c.CustomerId
      AND a.AddressType = 'PRIMARY'
);
```

## Checkpoint

Przy migracji batchowej zapisuj postęp.

```sql
CREATE TABLE migration.Progress
(
    MigrationName sysname NOT NULL PRIMARY KEY,
    LastKey bigint NULL,
    UpdatedAt datetime2(0) NOT NULL
);
```

## Transakcja per batch

Nie musisz obejmować całej migracji jedną wielogodzinną transakcją.

Małe transakcje:

- ograniczają log,
- skracają rollback,
- ułatwiają restart,
- zmniejszają czas blokad.

## Reconciliation

Idempotencja nie zwalnia z walidacji.

Po każdym etapie porównuj:

- liczbę rekordów,
- sumy kontrolne tam, gdzie mają sens,
- brakujące klucze,
- duplikaty,
- błędy konwersji.

## Podsumowanie

Dobry skrypt migracyjny zakłada, że zostanie przerwany.

Najbezpieczniejsza migracja to taka, którą można wznowić bez zgadywania, co już się wydarzyło.