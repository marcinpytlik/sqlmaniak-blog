---
title: "Query Store przed zmianą Compatibility Level — jak przygotować bezpieczną migrację?"
date: 2026-09-29T20:00:00+02:00
slug: query-store-przed-zmiana-compatibility-level
description: "Jak użyć Query Store do zbudowania baseline przed zmianą Compatibility Level i wykrywania regresji planów zapytań po migracji SQL Server."
tags: [SQLServer, QueryStore, CompatibilityLevel, Migration, Performance]
categories: [SQL Server]
draft: false
---

Zmiana Compatibility Level może zmienić sposób optymalizacji zapytań.

Query Store pozwala porównać zachowanie zapytań przed i po zmianie.

## Włączenie Query Store

```sql
ALTER DATABASE [TwojaBaza]
SET QUERY_STORE = ON;
GO

ALTER DATABASE [TwojaBaza]
SET QUERY_STORE
(
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = AUTO,
    MAX_STORAGE_SIZE_MB = 2048,
    INTERVAL_LENGTH_MINUTES = 15,
    CLEANUP_POLICY =
    (
        STALE_QUERY_THRESHOLD_DAYS = 30
    )
);
GO
```

## Sprawdzenie stanu

```sql
SELECT
    actual_state_desc,
    desired_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason,
    query_capture_mode_desc
FROM sys.database_query_store_options;
```

## Jak długo zbierać baseline?

Baseline powinien obejmować:

- zwykłe dni robocze,
- okresy szczytu,
- procesy nocne,
- zamknięcie miesiąca,
- ETL,
- raporty okresowe.

## Zmiana Compatibility Level

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

Zmianę wykonuj jako osobny etap, po testach i z przygotowanym rollbackiem.

## Wymuszenie wcześniejszego planu

```sql
EXEC sys.sp_query_store_force_plan
    @query_id = 123,
    @plan_id = 456;
```

Plan forcing może być działaniem stabilizującym, ale powinien być monitorowany i udokumentowany.

## Plan migracji

1. Włącz Query Store.
2. Zweryfikuj konfigurację.
3. Zbierz reprezentatywny baseline.
4. Zapisz listę krytycznych zapytań.
5. Przeprowadź test.
6. Zmień Compatibility Level.
7. Monitoruj regresje.
8. Stabilizuj krytyczne zapytania.
9. Dokumentuj forcing.
10. Wdrażaj trwałe poprawki.

## Podsumowanie

Query Store nie usuwa ryzyka, ale zamienia zgadywanie w analizę danych.

Spokojny DBA nie zmienia Compatibility Level bez punktu odniesienia.

Najpierw buduje baseline.
