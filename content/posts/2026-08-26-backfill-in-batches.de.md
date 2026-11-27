---
title: "Backfill in Batches: Millionen Datensätze ohne eine riesige Transaktion migrieren"
date: 2026-08-25T00:01:00+02:00
slug: "backfill-in-batches-sql-server"
description: "Praxisorientierte Migration von SQL-Server-Daten und Befüllung neuer Spalten in kleinen Batches."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - Backfill
  - Datenmigration
  - Transaktionslog
  - Sperren
draft: false
---

# Backfill in Batches: Millionen Datensätze ohne eine riesige Transaktion migrieren

Das Hinzufügen einer neuen Spalte ist oft erst der Anfang einer Schemaänderung. Danach müssen historische Datensätze mit Werten gefüllt werden.

Die einfachste Lösung:

```sql
UPDATE dbo.Orders
SET OrderSource = 'Legacy'
WHERE OrderSource IS NULL;
```

Bei einigen Tausend Zeilen kann das gut funktionieren. Bei Hunderten Millionen Zeilen drohen jedoch:

- starkes Wachstum des Transaktionslogs,
- lang gehaltene Sperren,
- Lock Escalation,
- Verzögerungen bei Replikation oder Availability Groups,
- aufwendiger Rollback nach einer Unterbrechung,
- Auswirkungen auf Backups und Wartungsfenster.

Das Muster **Backfill in Batches** teilt die Arbeit in kleine, wiederholbare Transaktionen.

> Ziel ist nicht die schnellstmögliche Migration. Ziel ist eine Geschwindigkeit, die das Produktionssystem sicher verkraftet.

## Beispielschema

```sql
CREATE TABLE dbo.Orders
(
    OrderId     bigint IDENTITY(1,1) NOT NULL,
    CustomerId  int NOT NULL,
    CreatedAt   datetime2(0) NOT NULL,
    OrderSource varchar(30) NULL,

    CONSTRAINT PK_Orders
        PRIMARY KEY (OrderId)
);
```

Die neue Spalte `OrderSource` erlaubt zunächst `NULL`, damit nicht sofort die gesamte Tabelle umgeschrieben werden muss.

## Die einfachste Schleife

```sql
WHILE 1 = 1
BEGIN
    UPDATE TOP (5000) dbo.Orders
    SET OrderSource = 'Legacy'
    WHERE OrderSource IS NULL;

    IF @@ROWCOUNT = 0
        BREAK;
END;
```

Das ist besser als eine einzige riesige Transaktion, aber noch nicht ideal. Jeder Batch kann erneut einen großen Teil der Tabelle scannen.

## Migration anhand des Schlüssels

Eine bessere Variante merkt sich den zuletzt verarbeiteten Schlüssel:

```sql
DECLARE
    @BatchSize   int = 5000,
    @LastOrderId bigint = 0,
    @MaxOrderId  bigint;

SELECT @MaxOrderId = MAX(OrderId)
FROM dbo.Orders;

WHILE @LastOrderId < @MaxOrderId
BEGIN
    UPDATE dbo.Orders
    SET OrderSource = 'Legacy'
    WHERE OrderId > @LastOrderId
      AND OrderId <= @LastOrderId + @BatchSize
      AND OrderSource IS NULL;

    SET @LastOrderId += @BatchSize;
END;
```

Diese Variante ist gut vorhersehbar, setzt aber relativ fortlaufende Schlüssel voraus. Bei großen Lücken sollten die tatsächlichen IDs der Batches ermittelt werden.

```sql
DECLARE @BatchSize int = 5000;

WHILE 1 = 1
BEGIN
    CREATE TABLE #Batch
    (
        OrderId bigint NOT NULL PRIMARY KEY
    );

    INSERT INTO #Batch(OrderId)
    SELECT TOP (@BatchSize)
        o.OrderId
    FROM dbo.Orders AS o WITH (READPAST)
    WHERE o.OrderSource IS NULL
    ORDER BY o.OrderId;

    IF @@ROWCOUNT = 0
        BREAK;

    UPDATE o
    SET OrderSource = 'Legacy'
    FROM dbo.Orders AS o
    JOIN #Batch AS b
        ON b.OrderId = o.OrderId;

    DROP TABLE #Batch;
END;
```

**Praxis-Hinweis:** Dieses Demonstrationsskript erstellt `#Batch` innerhalb der Schleife und verlässt sie beim letzten Durchlauf vor dem Löschen der Tabelle. In einer produktiven Implementierung muss die temporäre Tabelle zuverlässig bereinigt und das Verhalten von `READPAST` mit dem verwendeten Isolationsmodell abgestimmt werden. Ein temporärer gefilterter Index kann wiederholte Scans vermeiden.

## Wiederaufnehmbarkeit

Ein Neustart, Deployment oder Wartungsfenster kann den Prozess unterbrechen. Er sollte deshalb wiederaufnehmbar sein.

Eine Steuertabelle hilft:

```sql
CREATE TABLE dbo.DataMigrationState
(
    MigrationName   sysname NOT NULL,
    LastProcessedId bigint NOT NULL,
    RowsProcessed   bigint NOT NULL,
    LastBatchAt     datetime2(0) NULL,
    CompletedAt     datetime2(0) NULL,

    CONSTRAINT PK_DataMigrationState
        PRIMARY KEY (MigrationName)
);
```

Nach jedem Batch wird der Status aktualisiert. Damit ist bekannt:

- wo der Prozess angehalten wurde,
- wie viele Datensätze verarbeitet wurden,
- wann der letzte Batch abgeschlossen wurde,
- ob die Migration fertig ist.

## Batchgröße

Es gibt keinen universell richtigen Wert. `100`, `5000` oder `50000` können sinnvoll sein, abhängig von:

- Zeilenbreite,
- Anzahl der Indizes,
- Art des Updates,
- Storage-Performance,
- Systemlast,
- Log-Durchsatz,
- Replikation und Hochverfügbarkeit.

Beginne mit kleinen Batches und beobachte:

- Batchdauer,
- protokollierte Bytes,
- Sperren,
- Replikaverzögerung,
- CPU- und I/O-Auslastung.

## Geschwindigkeit steuern

Eine Pause ist möglich:

```sql
WAITFOR DELAY '00:00:00.250';
```

Außerdem kann die Migration bei hoher Last oder zu großer Replikaverzögerung angehalten werden. Das Throttling sollte einfach und vorhersehbar bleiben.

## Unterstützender Index

Das Prädikat:

```sql
WHERE OrderSource IS NULL
```

kann einen vollständigen Scan erfordern. Ein temporärer gefilterter Index kann die Migration erheblich beschleunigen:

```sql
CREATE INDEX IX_Orders_Backfill_OrderSource
ON dbo.Orders(OrderId)
WHERE OrderSource IS NULL;
```

Nach Abschluss entfernen:

```sql
DROP INDEX IX_Orders_Backfill_OrderSource
ON dbo.Orders;
```

Dabei sind der Aufwand des Indexaufbaus und die zusätzlichen Schreibkosten während der Migration zu berücksichtigen.

## Gleichzeitige Schreibzugriffe der Anwendung

Fügt die Anwendung neue Datensätze ein, sollte sie die neue Spalte sofort befüllen. Andernfalls läuft der Backfill ständig neuen `NULL`-Werten hinterher.

Typische Reihenfolge:

1. Spalte als nullable hinzufügen.
2. Anwendung deployen, die den neuen Wert schreibt.
3. Historische Datensätze per Backfill migrieren.
4. Prüfen, dass keine `NULL`-Werte übrig sind.
5. `NOT NULL` setzen.

## Validierung

Nach der Migration reicht „Job erfolgreich beendet“ nicht aus.

```sql
SELECT COUNT_BIG(*) AS MissingRows
FROM dbo.Orders
WHERE OrderSource IS NULL;
```

Das Ergebnis muss null sein.

Zusätzlich empfiehlt sich der Vergleich von Aggregaten, Prüfsummen oder abgeleiteten Werten aus altem und neuem Modell.

## Und der Rollback?

Jeder Batch ist eine eigene Transaktion. Ein Rollback betrifft daher nur den aktuellen Batch. Bereits abgeschlossene Batches werden nicht automatisch rückgängig gemacht.

Vorher muss geklärt sein, ob:

- der neue Wert erneut berechnet werden kann,
- eine Änderungstabelle benötigt wird,
- die Migration umkehrbar ist,
- Fehler durch eine Vorwärtskorrektur behoben werden.

## Wann einsetzen?

Backfill in Batches eignet sich, wenn:

- die Tabelle groß ist,
- das System verfügbar bleiben muss,
- das Update Log und Sperren belastet,
- die Migration Stunden oder Tage dauert,
- der Prozess nach Unterbrechungen fortgesetzt werden muss.

## Wann ist eine Transaktion besser?

Bei einer kleinen Tabelle kann ein einfaches `UPDATE` übersichtlicher und sicherer sein. Migrationen sollten nicht unnötig kompliziert werden. Zuerst müssen Datenmenge und Operationskosten bekannt sein.

## Zusammenfassung

Backfill in Batches ist ein operatives Muster. Die `UPDATE`-Anweisung ist nicht der schwierigste Teil. Die Herausforderung liegt darin, die Auswirkungen auf das laufende System zu kontrollieren.

Eine gute Batchmigration ist:

- wiederaufnehmbar,
- idempotent,
- überwacht,
- validiert,
- an die Last angepasst,
- durch Entfernung temporärer Mechanismen abgeschlossen.

Millionen Datensätze müssen keine riesige Transaktion bedeuten. Es können Tausende kleiner, vorhersehbarer Schritte sein.
