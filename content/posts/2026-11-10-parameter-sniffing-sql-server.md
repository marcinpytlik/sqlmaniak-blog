---
title: "Parameter Sniffing — kiedy ten sam plan jest dobry dla jednego parametru, a zły dla drugiego"
date: 2026-11-10T20:00:00+01:00
slug: parameter-sniffing-sql-server
description: "Praktyczne wyjaśnienie Parameter Sniffing w SQL Server: jak rozpoznać problem, jak go mierzyć i kiedy rozważyć PSP, RECOMPILE lub inne rozwiązanie."
tags: [SQLServer, ParameterSniffing, Performance, QueryTuning, DBA]
categories: [SQL Server]
draft: false
---

Parameter Sniffing sam w sobie nie jest błędem.

SQL Server podczas kompilacji procedury może wykorzystać wartości parametrów do przygotowania planu. Problem zaczyna się wtedy, gdy rozkład danych jest nierówny.

## Przykład

```sql
CREATE OR ALTER PROCEDURE dbo.GetOrdersByCustomer
    @CustomerId int
AS
BEGIN
    SELECT
        OrderId,
        CustomerId,
        OrderDate,
        TotalAmount
    FROM dbo.Orders
    WHERE CustomerId = @CustomerId;
END;
GO
```

Jeżeli jeden klient ma 5 zamówień, a drugi 5 milionów, jeden plan może nie być dobry dla obu.

## Typowe objawy

- procedura raz działa szybko, a raz bardzo wolno,
- restart lub recompile pomaga tylko na jakiś czas,
- plan zmienia się po wdrożeniu albo failover,
- czas wykonania zależy od pierwszej wartości parametru,
- Query Store pokazuje dużą zmienność.

## RECOMPILE

```sql
OPTION (RECOMPILE);
```

Plan powstaje ponownie, ale płacisz kosztem kompilacji.

## OPTIMIZE FOR

```sql
OPTION (OPTIMIZE FOR UNKNOWN);
```

To nie jest rozwiązanie uniwersalne. Musi pasować do rzeczywistego rozkładu danych.

## Parameter Sensitive Plan

W SQL Server 2022 przy odpowiednim Compatibility Level silnik może korzystać z Parameter Sensitive Plan optimization i utrzymywać kilka wariantów planu dla różnych klas parametrów.

## Podsumowanie

Jeżeli procedura raz działa dobrze, a raz źle, nie zaczynaj od restartu.

Sprawdź parametry, rozkład danych i historię planów.