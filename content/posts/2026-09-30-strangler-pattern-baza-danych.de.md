---
title: "Strangler Pattern für Datenbanken: das alte Modell ohne großen Cutover ablösen"
date: 2026-09-30T00:01:00+02:00
slug: strangler-pattern-datenbank
description: "Ein altes Datenmodell schrittweise ersetzen, ohne einen einzigen riskanten Migrationszeitpunkt."
category: "Relationaler Renaissance"
tags: [SQL Server, schema evolution, strangler pattern, Datenmigration, database DevOps]
draft: false
---

# Strangler Pattern für Datenbanken: das alte Modell ohne großen Cutover ablösen

Nach Feature Flags stellt sich die nächste Frage: **Wie lässt sich das alte Modell ohne einen einzigen großen Cutover abschalten?**

Ein Ansatz ist das Strangler Pattern. Ein neuer Systemteil übernimmt nach und nach die Verantwortung für weitere Operationen, bis die alte Struktur nicht mehr gebraucht wird.

> Migriere nicht alles auf einmal. Übertrage Verantwortung Stück für Stück.

## Beispiel

Altes Modell:

```sql
CREATE TABLE dbo.Customer
(
    CustomerId int NOT NULL PRIMARY KEY,
    Name nvarchar(200) NOT NULL,
    AddressText nvarchar(500) NULL
);
```

Neues Modell:

```sql
CREATE TABLE dbo.CustomerAddress
(
    CustomerAddressId bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
    CustomerId int NOT NULL,
    AddressLine1 nvarchar(200) NOT NULL,
    City nvarchar(100) NOT NULL,
    PostalCode nvarchar(20) NULL
);
```

## Phase 1 — Neue Schreibvorgänge

Zunächst leiten wir neue Operationen zum neuen Modell und halten das alte kompatibel.

Eine Zeit lang können wir verwenden:

- Dual Write,
- Schreiben ins neue Modell mit Rücksynchronisierung,
- eine Ereigniswarteschlange zur Aktualisierung der alten Struktur.

## Phase 2 — Neue Lesezugriffe

Anschließend wechseln ausgewählte Lesezugriffe zur neuen Tabelle. Eine Feature Flag begrenzt den Umfang.

Zunächst können Shadow Reads durchgeführt und Ergebnisse verglichen werden, ohne Benutzer zu beeinflussen.

## Phase 3 — Das alte Modell isolieren

Anwendungen sollten nicht mehr direkt auf die alte Tabelle zugreifen.

Hilfreich sind:

- Kompatibilitätsviews,
- Stored Procedures als Zugriffsschicht,
- ein eigenes `legacy`-Schema,
- Monitoring von Abfragen auf das alte Objekt.

## Phase 4 — Abschaltung

Das alte Modell wird erst entfernt, wenn nachgewiesen ist, dass:

- keine aktiven Lesezugriffe mehr existieren,
- keine aktiven Schreibvorgänge mehr existieren,
- das Backfill erfolgreich abgeschlossen wurde,
- Integrationen umgestellt wurden,
- ein Rollback die alte Struktur nicht mehr benötigt.

## Das größte Risiko

Das Strangler Pattern scheitert, wenn altes und neues Modell zu lange gleichberechtigte Sources of Truth bleiben.

Für jede Migrationsphase muss eindeutig feststehen, welches Modell maßgeblich ist.

## Zusammenfassung

Das Strangler Pattern ersetzt eine große Migration durch eine Reihe kleiner, kontrollierter Verantwortungsübergaben.

Die relationale Renaissance bedeutet keine Revolution. Sie bedeutet, dass das alte Modell auf kontrollierte Weise überflüssig wird.
