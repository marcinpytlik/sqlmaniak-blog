---
title: "Parameter Sniffing — wenn derselbe Ausführungsplan für einen Parameter gut und für einen anderen schlecht ist"
date: 2026-11-10T08:00:00+01:00
slug: parameter-sniffing-sql-server
description: "Parameter Sniffing in SQL Server praxisnah erklärt: Probleme erkennen und messen sowie PSP, RECOMPILE und weitere Lösungsansätze beurteilen."
tags: [SQLServer, ParameterSniffing, Performance, QueryTuning, DBA]
categories: [SQL Server]
draft: false
---

Parameter Sniffing ist an sich kein Fehler.

Beim Kompilieren einer gespeicherten Prozedur kann SQL Server die übergebenen Parameterwerte nutzen, um einen Ausführungsplan zu erstellen. Problematisch wird es, wenn die Daten ungleich verteilt sind.

## Beispiel

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

Hat ein Kunde 5 Bestellungen und ein anderer 5 Millionen, ist ein einziger Ausführungsplan möglicherweise nicht für beide geeignet.

## Typische Symptome

- Die Prozedur läuft manchmal schnell und manchmal sehr langsam.
- Ein Neustart oder eine Neukompilierung hilft nur vorübergehend.
- Nach einem Deployment oder Failover ändert sich der Ausführungsplan.
- Die Ausführungszeit hängt vom Parameterwert ab, mit dem der Plan zuerst kompiliert wurde.
- Query Store zeigt starke Schwankungen.

## RECOMPILE

```sql
OPTION (RECOMPILE);
```

Der Ausführungsplan wird neu erstellt. Dafür fallen zusätzliche Kompilierungskosten an.

## OPTIMIZE FOR

```sql
OPTION (OPTIMIZE FOR UNKNOWN);
```

Das ist keine Universallösung. Der Ansatz muss zur tatsächlichen Datenverteilung passen.

## Parameter Sensitive Plan

In SQL Server 2022 kann die Engine bei einem geeigneten Kompatibilitätsgrad die Parameter Sensitive Plan (PSP) Optimization verwenden und mehrere Planvarianten für unterschiedliche Parameterwertbereiche bereitstellen.

## Fazit

Wenn eine Prozedur einmal gut und einmal schlecht läuft, sollte ein Serverneustart nicht die erste Maßnahme sein.

Untersuchen Sie die Parameterwerte, die Datenverteilung und die Historie der Ausführungspläne.
