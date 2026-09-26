---
title: "Compatibility Level po migracji — dlaczego nie warto zmieniać go od razu"
date: 2026-10-27T20:00:00+01:00
slug: compatibility-level-po-migracji
description: "Jak bezpiecznie podejść do zmiany Compatibility Level po migracji SQL Server: Query Store, baseline, regresje planów i plan wycofania."
tags: [SQLServer, Migration, CompatibilityLevel, QueryStore, DBA]
categories: [SQL Server]
draft: false
---

Przeniesienie bazy na SQL Server 2022 nie oznacza, że od razu trzeba ustawić `COMPATIBILITY_LEVEL = 160`.

To są dwa osobne kroki i warto je tak traktować.

## Najpierw sprawdź aktualny poziom

```sql
SELECT
    name,
    compatibility_level
FROM sys.databases
WHERE database_id > 4
ORDER BY name;
```

Baza może działać na SQL Server 2022 i nadal mieć Compatibility Level 130. Dzięki temu migrację silnika można oddzielić od zmian zachowania optymalizatora.

## Dlaczego to ma znaczenie?

Zmiana Compatibility Level może wpływać między innymi na:

- Cardinality Estimator,
- scalar UDF inlining,
- table variable deferred compilation,
- batch mode on rowstore,
- memory grant feedback,
- Parameter Sensitive Plan optimization.

Nie każda zmiana spowoduje regresję, ale każda powinna być obserwowana.

## Query Store przed zmianą

```sql
SELECT
    actual_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason
FROM sys.database_query_store_options;
```

Przed zmianą zbierz baseline: najdroższe zapytania, CPU, logical reads, czasy wykonania, waity i najważniejsze plany.

## Zmiana Compatibility Level

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

Po zmianie nie oceniaj systemu tylko po tym, że aplikacja się uruchomiła. Obserwuj zachowanie pod realnym obciążeniem.

## Plan wycofania

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 130;
```

Zmiana jest odwracalna, ale rollback nie powinien być pierwszą reakcją. Najpierw ustal, czy problem dotyczy konkretnego zapytania.

## Podsumowanie

Migracja i Compatibility Level to dwa różne etapy.

Spokojny DBA najpierw przenosi system, stabilizuje go, zbiera baseline, a dopiero potem świadomie włącza nowe zachowania optymalizatora.