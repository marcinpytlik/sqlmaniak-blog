---
title: "CDC jako narzędzie migracji: backfill to dopiero początek"
date: 2026-10-07T00:01:00+02:00
slug: "cdc-jako-narzedzie-migracji"
description: "Jak wykorzystać Change Data Capture do synchronizacji delty podczas migracji dużych tabel i zmian modelu danych."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - CDC
  - migracja danych
  - schema evolution
  - database DevOps
draft: false
---

# CDC jako narzędzie migracji: backfill to dopiero początek

Przy dużej tabeli nie da się zawsze zrobić jednego `INSERT ... SELECT` i zatrzymać aplikacji na kilka godzin.

Potrzebujemy dwóch elementów:

1. backfill danych historycznych,
2. synchronizacji zmian, które pojawiają się w trakcie migracji.

CDC może pomóc w drugim punkcie.

## Schemat procesu

```text
T0  uruchom CDC
T1  rozpocznij backfill
T2  aplikacja nadal zapisuje do starej tabeli
T3  odczytuj zmiany z CDC
T4  aplikuj deltę do nowego modelu
T5  wyrównaj opóźnienie
T6  przełącz odczyt i zapis
```

## Włączenie CDC

```sql
EXEC sys.sp_cdc_enable_db;
GO

EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'Orders',
    @role_name     = NULL,
    @supports_net_changes = 1;
GO
```

## LSN zamiast czasu

Nie opieraj synchronizacji na `ModifiedDate`, jeśli potrzebujesz pełnej kolejności zmian.

CDC pracuje na LSN. Dzięki temu można określić zakres:

```sql
DECLARE @from_lsn binary(10) = sys.fn_cdc_get_min_lsn(N'dbo_Orders');
DECLARE @to_lsn   binary(10) = sys.fn_cdc_get_max_lsn();
```

## Idempotencja

Proces synchronizacji powinien tolerować ponowne przetworzenie zakresu.

Najbezpieczniej przechowywać checkpoint, np.:

```sql
CREATE TABLE migration.CdcCheckpoint
(
    PipelineName sysname NOT NULL PRIMARY KEY,
    LastProcessedLsn binary(10) NOT NULL,
    UpdatedAt datetime2(0) NOT NULL
);
```

## Problem z cleanup

CDC nie przechowuje zmian bez końca. Job cleanup usuwa stare wpisy.

Jeżeli pipeline migracyjny przestanie działać na zbyt długo, wymagany zakres może zniknąć.

Monitoring powinien więc obejmować:

- najstarszy dostępny LSN,
- ostatni przetworzony LSN,
- opóźnienie pipeline,
- liczbę błędów,
- tempo przyrostu zmian.

## Moment przełączenia

Przed przełączeniem sprawdź, czy delta została wyrównana do akceptowalnego poziomu.

To może oznaczać:

- krótkie zatrzymanie zapisów,
- finalny odczyt CDC,
- zastosowanie ostatniej delty,
- przełączenie aplikacji.

## CDC nie jest magiczną replikacją

CDC zapisuje informacje o zmianach. To Ty odpowiadasz za ich interpretację i zastosowanie do nowego modelu.

Jeżeli jedna operacja w starym modelu staje się trzema operacjami w nowym, logika migracji musi to rozumieć.

## Podsumowanie

Backfill daje stan historyczny. CDC pozwala śledzić to, co zmienia się w czasie migracji.

Razem tworzą podstawę migracji online, ale wymagają checkpointów, monitoringu i jednoznacznego momentu przełączenia.