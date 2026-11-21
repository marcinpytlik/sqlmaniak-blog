---
title: "Datentyp ohne große Blockierung ändern: Neue Spalte statt ALTER COLUMN"
date: 2026-11-11T08:00:00+01:00
slug: datentyp-sicher-migrieren-neue-spalte
description: "Wie man Datentypen in großen Tabellen schrittweise ändert, statt ein riskantes ALTER COLUMN im laufenden System auszuführen."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - Schema-Evolution
  - Datentyp
  - Zero Downtime
  - Database DevOps
draft: false
---

# Datentyp ohne große Blockierung ändern: Neue Spalte statt ALTER COLUMN

`ALTER COLUMN` wirkt harmlos – bis eine Tabelle Hunderte Millionen Zeilen enthält.

Eine Änderung des Datentyps kann den Neuaufbau von Daten, Indizes und Abhängigkeiten erforderlich machen.

## Beispiel

Wir möchten von:

```text
OrderNumber varchar(20)
```

zu:

```text
OrderNumber bigint
```

wechseln.

## Schritt 1 — Neue Spalte anlegen

```sql
ALTER TABLE dbo.Orders
ADD OrderNumberBigint bigint NULL;
```

## Schritt 2 — Konvertierung prüfen

```sql
SELECT OrderNumber
FROM dbo.Orders
WHERE TRY_CONVERT(bigint, OrderNumber) IS NULL
  AND OrderNumber IS NOT NULL;
```

Zuerst ermitteln wir die Datensätze, die sich nicht migrieren lassen.

## Schritt 3 — Daten in Batches übernehmen

```sql
UPDATE TOP (10000) dbo.Orders
SET OrderNumberBigint = TRY_CONVERT(bigint, OrderNumber)
WHERE OrderNumberBigint IS NULL
  AND OrderNumber IS NOT NULL;
```

## Schritt 4 — Dual Write

Die neue Anwendungsversion schreibt beide Darstellungen oder schreibt eine davon und synchronisiert die andere.

## Schritt 5 — Lesezugriffe umstellen

Nach der Validierung wird die neue Spalte für Lesezugriffe verwendet.

## Indizes

Vergiss nicht, Indizes, die von der alten Spalte abhängen, gesondert einzuplanen.

Der neue Index lässt sich bereits vor der Umstellung anlegen:

```sql
CREATE INDEX IX_Orders_OrderNumberBigint
ON dbo.Orders(OrderNumberBigint);
```

## Contract

Die alte Spalte wird erst entfernt, wenn:

- alle Lesezugriffe die neue Spalte nutzen,
- alle Schreibzugriffe die neue Spalte nutzen,
- sämtliche Integrationen umgestellt sind,
- die Daten validiert wurden,
- für einen Rollback die alte Darstellung nicht mehr benötigt wird.

## Fazit

Die Änderung eines Datentyps muss nicht aus einer einzigen DDL-Operation bestehen.

Eine neue Spalte, schrittweise Datenübernahme, Validierung und Umstellung bieten deutlich mehr Kontrolle über das Risiko.