---
title: "Scalanie tabel bez przestoju: kiedy dwa modele mają stać się jednym"
date: 2026-11-04T00:01:00+01:00
slug: "scalanie-tabel-bez-przestoju"
description: "Jak bezpiecznie scalić dane z kilku tabel w jeden nowy model bez jednorazowego przełączenia całej aplikacji."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - schema evolution
  - migracja danych
  - zero downtime
  - database DevOps
draft: false
---

# Scalanie tabel bez przestoju: kiedy dwa modele mają stać się jednym

Podział tabeli to jeden kierunek. Czasem po latach chcemy zrobić odwrotnie: kilka struktur połączyć w jeden model.

## Przykład

Mamy:

```text
RetailCustomer
BusinessCustomer
```

i chcemy przejść do:

```text
Customer
```

## Nowy model

```sql
CREATE TABLE dbo.CustomerV2
(
    CustomerId bigint NOT NULL PRIMARY KEY,
    CustomerType varchar(20) NOT NULL,
    DisplayName nvarchar(200) NOT NULL,
    TaxId nvarchar(30) NULL
);
```

## Najpierw mapowanie semantyki

Scalenie nie jest tylko `UNION ALL`.

Trzeba ustalić:

- jak mapują się klucze,
- które kolumny mają wspólne znaczenie,
- co zrobić z kolizjami identyfikatorów,
- jak reprezentować pola istniejące tylko w jednym modelu.

## Stabilny klucz

Jeżeli stare tabele mogą mieć ten sam `CustomerId`, potrzebna jest warstwa mapowania.

```sql
CREATE TABLE migration.CustomerKeyMap
(
    SourceType varchar(20) NOT NULL,
    SourceId bigint NOT NULL,
    TargetId bigint NOT NULL,
    CONSTRAINT PK_CustomerKeyMap
        PRIMARY KEY (SourceType, SourceId)
);
```

## Backfill i delta

Najpierw przenosimy stan historyczny. Potem synchronizujemy zmiany przychodzące w trakcie procesu.

CDC, kolejka zdarzeń albo dual-write mogą pełnić tę rolę.

## Przełączanie konsumentów

Nie wszystkie aplikacje muszą przejść jednocześnie.

Można najpierw przełączyć:

- nowe API,
- raporty,
- wybrany moduł aplikacji,
- procesy batchowe.

## Największa pułapka

Nie usuwaj starych tabel tylko dlatego, że nowa została poprawnie zasilona.

Najpierw udowodnij, że nikt już nie korzysta ze starego kontraktu.

## Podsumowanie

Scalanie tabel to migracja danych, kluczy i semantyki jednocześnie.

Bez mapowania i telemetrii łatwo uzyskać nowy model, którego nie da się bezpiecznie zweryfikować.