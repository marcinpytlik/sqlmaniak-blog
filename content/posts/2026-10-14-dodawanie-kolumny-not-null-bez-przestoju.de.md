---
title: "NOT NULL ohne Ausfallzeit: Eine Pflichtspalte sicher hinzufügen"
date: 2026-10-14T00:01:00+02:00
slug: not-null-spalte-ohne-ausfallzeit-hinzufuegen
description: "Ein sicheres Vorgehen, um einer großen Tabelle eine Pflichtspalte hinzuzufügen, ohne alles in einer riskanten Bereitstellung zu ändern."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - Schema-Evolution
  - NOT NULL
  - Zero Downtime
  - Database DevOps
draft: false
---

# NOT NULL ohne Ausfallzeit: Eine Pflichtspalte sicher hinzufügen

Eine scheinbar einfache Änderung:

```sql
ALTER TABLE dbo.Orders
ADD SourceSystem varchar(20) NOT NULL;
```

kann bei einer großen Tabelle alles andere als einfach sein.

Sicherer ist es, sie in mehrere Schritte aufzuteilen.

## Schritt 1 — NULL-Werte zunächst zulassen

```sql
ALTER TABLE dbo.Orders
ADD SourceSystem varchar(20) NULL;
```

Der alte Code funktioniert weiterhin, weil er die neue Spalte noch nicht kennen muss.

## Schritt 2 — Der neue Code schreibt einen Wert

Ab diesem Zeitpunkt sollte jeder neue Datensatz einen Wert für `SourceSystem` erhalten.

Fehlende Werte lassen sich überwachen:

```sql
SELECT COUNT(*) AS MissingValueCount
FROM dbo.Orders
WHERE SourceSystem IS NULL;
```

## Schritt 3 — Backfill

Wir ergänzen historische Daten in Batches.

```sql
WHILE 1 = 1
BEGIN
    UPDATE TOP (10000) dbo.Orders
    SET SourceSystem = 'LEGACY'
    WHERE SourceSystem IS NULL;

    IF @@ROWCOUNT = 0 BREAK;

    WAITFOR DELAY '00:00:00.200';
END;
```

Die Batchgröße sollte anhand von Transaktionslog, Sperren und Ausführungszeit festgelegt werden.

## Schritt 4 — Validierung

```sql
SELECT COUNT(*)
FROM dbo.Orders
WHERE SourceSystem IS NULL;
```

Null fehlende Werte sind erst der Anfang. Außerdem muss bestätigt werden, dass alle aktiven Anwendungsversionen einen Wert schreiben.

## Schritt 5 — NOT NULL erzwingen

```sql
ALTER TABLE dbo.Orders
ALTER COLUMN SourceSystem varchar(20) NOT NULL;
```

Das sollte ein eigener Deployment-Schritt sein.

## Und was ist mit DEFAULT?

Ein Standardwert kann bei neuen Datensätzen helfen:

```sql
ALTER TABLE dbo.Orders
ADD CONSTRAINT DF_Orders_SourceSystem
DEFAULT ('APP') FOR SourceSystem;
```

Er sollte jedoch nicht ohne bewusste Entscheidung einen Fehler der Anwendung verdecken.

## Die wichtigste Regel

Sorge zuerst dafür, dass die Einschränkung **fachlich und in den tatsächlichen Daten gilt**. Erst danach erzwingst du sie technisch.

## Fazit

Die Änderung von `NULL -> NOT NULL` muss nicht in einem einzigen Befehl erfolgen.

Expand, neue Werte schreiben, Backfill, Validierung und erst dann die Einschränkung — das ist der deutlich kontrolliertere Weg.