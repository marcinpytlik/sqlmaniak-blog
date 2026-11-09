---
title: "Eine Tabelle ohne Big Bang aufteilen: Aus einem Datenmodell werden zwei"
date: 2026-10-28T08:00:00+01:00
slug: "tabelle-aufteilen-ohne-big-bang"
description: "Wie man eine breite Tabelle sicher in zwei Strukturen aufteilt, ohne Anwendung und Daten in einem einzigen großen Schritt umzustellen."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - Schema-Evolution
  - Normalisierung
  - Datenmigration
  - Database DevOps
draft: false
---

Nehmen wir an, dass die Tabelle `Customer` im Laufe der Jahre auf mehrere Dutzend Spalten angewachsen ist.

Einen Teil der Adressdaten möchten wir in eine eigene Tabelle auslagern.

## Die neue Tabelle

```sql
CREATE TABLE dbo.CustomerAddress
(
    CustomerId int NOT NULL,
    AddressType varchar(20) NOT NULL,
    AddressLine1 nvarchar(200) NOT NULL,
    City nvarchar(100) NOT NULL,
    PostalCode nvarchar(20) NULL,
    CONSTRAINT PK_CustomerAddress
        PRIMARY KEY (CustomerId, AddressType)
);
```

## Schritt 1 — Die neue Struktur ergänzen, ohne die alte zu entfernen

Die bisherigen Spalten bleiben bestehen. Die neue Tabelle erweitert zunächst das Datenmodell.

## Schritt 2 — Bestehende Daten übernehmen (Backfill)

```sql
INSERT dbo.CustomerAddress
(
    CustomerId, AddressType, AddressLine1, City, PostalCode
)
SELECT
    CustomerId, 'PRIMARY', AddressLine1, City, PostalCode
FROM dbo.Customer
WHERE AddressLine1 IS NOT NULL;
```

Bei großen Tabellen führen wir die Übernahme in Batches durch und speichern den Fortschritt mithilfe von Checkpoints.

## Schritt 3 — Beide Modelle synchron halten

Während der Übergangsphase muss eine Adressänderung entweder in beiden Modellen ankommen oder in einer führenden Datenquelle erfolgen, von der aus das andere Modell synchronisiert wird.

## Schritt 4 — Lesezugriffe umstellen

Zunächst leiten wir nur einen kleinen Teil der Zugriffe auf das neue Modell und erhöhen den Anteil schrittweise.

Mit Shadow Reads lassen sich die Ergebnisse der alten und der neuen Darstellung vergleichen.

## Schritt 5 — Die alten Spalten entfernen

Das ist der letzte Schritt und gehört nicht zum ersten Deployment.

Vor der Contract-Phase prüfen wir:

- Berichte,
- Integrationen,
- ETL-Prozesse,
- gespeicherte Prozeduren,
- dynamisches SQL,
- Exporte,
- BI-Werkzeuge.

## Semantische Risiken

Die Aufteilung einer Tabelle verändert häufig nicht nur das physische Schema, sondern auch die Bedeutung der Daten.

Aus einer Adresse können mehrere Adressen werden. In diesem Fall kann ein Rollback auf das alte Modell mit Informationsverlust verbunden sein.

## Fazit

Eine Tabellenaufteilung ist dann am sichersten, wenn wir zuerst die neue Darstellung ergänzen, anschließend die Zugriffe umstellen und erst ganz am Ende die alte Struktur entfernen.
