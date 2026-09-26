---
title: "Zmiana nazwy kolumny bez łamania aplikacji"
date: 2026-10-21T00:01:00+02:00
slug: "zmiana-nazwy-kolumny-bez-lamania-aplikacji"
description: "Jak zmienić nazwę kolumny w SQL Server bez natychmiastowego zerwania kompatybilności ze starszą wersją aplikacji."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - schema evolution
  - compatibility
  - deployment
  - database DevOps
draft: false
---

# Zmiana nazwy kolumny bez łamania aplikacji

`sp_rename` jest szybkie.

Problem w tym, że wszystkie zależności nie stają się automatycznie zgodne z nową nazwą.

## Ryzykowny wariant

```sql
EXEC sys.sp_rename
    N'dbo.Customer.Name',
    N'DisplayName',
    N'COLUMN';
```

Jeżeli stara aplikacja nadal odwołuje się do `Name`, przestaje działać natychmiast.

## Wariant kompatybilny

Zamiast rename:

1. dodaj nową kolumnę,
2. utrzymuj zgodność obu wartości,
3. przełącz kod,
4. usuń starą kolumnę dopiero później.

```sql
ALTER TABLE dbo.Customer
ADD DisplayName nvarchar(200) NULL;
```

## Backfill

```sql
UPDATE dbo.Customer
SET DisplayName = Name
WHERE DisplayName IS NULL;
```

Przy dużej tabeli wykonaj go partiami.

## Okres przejściowy

W tym czasie można zastosować:

- dual-write w aplikacji,
- trigger jako rozwiązanie przejściowe,
- procedurę aktualizującą oba pola,
- widok zgodności.

Trigger bywa wygodny, ale zwiększa ukrytą logikę i powinien mieć jasno określony termin usunięcia.

## Jak znaleźć zależności?

```sql
SELECT
    OBJECT_SCHEMA_NAME(referencing_id) AS SchemaName,
    OBJECT_NAME(referencing_id) AS ObjectName
FROM sys.sql_expression_dependencies
WHERE referenced_id = OBJECT_ID(N'dbo.Customer');
```

To nie wykryje wszystkiego, np. dynamicznego SQL poza bazą.

Potrzebne są też telemetryka i analiza aplikacji.

## Ostateczne usunięcie

Stara kolumna może zostać usunięta dopiero wtedy, gdy:

- stary kod nie działa już w żadnej instancji,
- nie ma raportów ani integracji używających starej nazwy,
- monitoring nie pokazuje odwołań,
- rollback nie wymaga starego kontraktu.

## Podsumowanie

Rename jest operacją techniczną. Migracja nazwy jest zmianą kontraktu.

W Relacyjnym Renesansie kontrakty zmieniamy etapami.