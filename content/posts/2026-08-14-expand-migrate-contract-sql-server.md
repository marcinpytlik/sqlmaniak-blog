---
title: "Expand–Migrate–Contract: SQL-Server-Schema sicher ohne Big-Bang-Migration verändern"
date: 2026-08-14T08:01:00+02:00
slug: "expand-migrate-contract-sql-server"
description: "Expand–Migrate–Contract ist ein Muster für sichere Schema-Evolution in SQL Server. Neue Strukturen werden zuerst hinzugefügt, Daten und Anwendungen schrittweise migriert und alte Strukturen erst nach erfolgreicher Validierung entfernt."
categories:
  - "Relationale Renaissance"
tags:
  - "SQL Server"
  - "SQL Server auf Deutsch"
  - "Schema Evolution"
  - "Expand Migrate Contract"
  - "Datenbankdesign"
  - "Datenmigration"
  - "Relationale Renaissance"
draft: false
---

Eine Schemaänderung sieht auf einem Whiteboard oft sehr einfach aus.

Eine Spalte wird nicht mehr benötigt.

Eine neue Tabelle soll entstehen.

Ein Attribut bekommt eine neue Struktur.

Technisch könnte die Lösung manchmal aus wenigen SQL-Anweisungen bestehen.

```sql
ALTER TABLE ...
```

In einem produktiven System ist jedoch selten die Syntax das eigentliche Problem.

Das Risiko entsteht durch die Komponenten, die das bestehende Schema bereits verwenden.

Anwendungen.

Stored Procedures.

Reports.

ETL-Prozesse.

Power-BI-Modelle.

SSIS-Pakete.

Integrationen.

Oder alte Skripte, an die sich niemand mehr erinnert.

Wenn wir das bestehende Schema sofort durch ein neues ersetzen, müssen alle diese Abhängigkeiten praktisch gleichzeitig umgestellt werden.

Genau dieses Problem adressiert das Muster:

## Expand–Migrate–Contract

Die Idee ist einfach:

1. **Expand** – das neue Modell hinzufügen, ohne das alte zu entfernen.
2. **Migrate** – Daten und Anwendungen schrittweise auf das neue Modell umstellen.
3. **Contract** – die alte Struktur erst entfernen, wenn sie nachweislich nicht mehr benötigt wird.

Damit wird eine Schemaänderung nicht als einzelnes Deployment behandelt.

Sie wird zu einem kontrollierten Prozess.

## Ausgangssituation

Nehmen wir eine einfache Kundentabelle:

```sql
CREATE TABLE dbo.Customers
(
    CustomerId   int IDENTITY(1,1) NOT NULL,
    CustomerName nvarchar(200) NOT NULL,
    AddressText  nvarchar(500) NULL,

    CONSTRAINT PK_Customers
        PRIMARY KEY (CustomerId)
);
```

Die komplette Adresse befindet sich in einer einzigen Spalte:

```text
ul. Długa 10, 00-001 Warszawa
```

Später möchten wir Adressen strukturiert speichern.

Zum Beispiel:

- Straße,
- Postleitzahl,
- Stadt,
- Land,
- Adresstyp.

Das neue Modell verwendet deshalb eine separate Tabelle:

```sql
CREATE TABLE dbo.CustomerAddresses
(
    CustomerAddressId bigint IDENTITY(1,1) NOT NULL,
    CustomerId        int NOT NULL,
    AddressLine1      nvarchar(200) NOT NULL,
    PostalCode        nvarchar(20) NULL,
    City              nvarchar(100) NULL,
    CountryCode       char(2) NOT NULL,

    CONSTRAINT PK_CustomerAddresses
        PRIMARY KEY (CustomerAddressId),

    CONSTRAINT FK_CustomerAddresses_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customers(CustomerId)
);
```

Die entscheidende Frage lautet jetzt nicht:

> Wie erstellen wir die neue Tabelle?

Die wichtigere Frage lautet:

> Wie kommen wir sicher vom alten zum neuen Modell?

## Phase 1: Expand

Während der Expand-Phase wird das bestehende Schema nicht zerstört.

Wir fügen lediglich die neue Struktur hinzu.

`Customers.AddressText` bleibt bestehen.

Zusätzlich entsteht:

`CustomerAddresses`.

Dadurch können alte Anwendungen weiterhin mit `AddressText` arbeiten.

Neue Komponenten können dagegen bereits das neue Modell verwenden.

Für eine gewisse Zeit existieren also beide Modelle parallel.

Das ist beabsichtigt.

Die temporäre Redundanz ermöglicht Rückwärtskompatibilität.

## Phase 2: Migrate

Jetzt beginnt die Migration.

Dabei müssen wir zwei unterschiedliche Probleme lösen.

### Historische Daten

Bestehende Werte aus:

```text
Customers.AddressText
```

müssen in:

```text
CustomerAddresses
```

übertragen werden.

Bei kleinen Tabellen kann eine einzelne Migration ausreichend sein.

Bei sehr großen Tabellen ist ein Backfill in Batches häufig sicherer.

Zum Beispiel:

```sql
UPDATE TOP (5000) ...
```

oder ein kontrollierter Prozess, der jeweils eine begrenzte Anzahl von Datensätzen verarbeitet.

Dadurch reduzieren wir unter anderem:

- lange Transaktionen,
- Sperren,
- Wachstum des Transaktionslogs,
- Belastung von Availability Groups oder Replikation,
- und die Kosten eines Rollbacks.

### Neue Schreibvorgänge

Während historische Daten migriert werden, läuft die Anwendung weiter.

Es entstehen also ständig neue oder geänderte Daten.

Deshalb müssen wir ebenfalls entscheiden, wie Schreiboperationen während der Übergangsphase behandelt werden.

Eine Möglichkeit ist **Dual Write**.

Dabei wird eine Geschäftsoperation sowohl in das alte als auch in das neue Modell geschrieben.

Dieses Muster betrachten wir im nächsten Artikel der Serie genauer.

## Anwendungen schrittweise umstellen

Ein großer Vorteil von Expand–Migrate–Contract besteht darin, dass nicht alle Anwendungen gleichzeitig geändert werden müssen.

Zum Beispiel:

1. Zuerst wird eine neue API auf `CustomerAddresses` umgestellt.
2. Danach folgen interne Prozesse.
3. Später werden Reports angepasst.
4. Anschließend können ältere Integrationen migriert werden.

Altes und neues Modell existieren währenddessen parallel.

Die Migration wird dadurch von einem Big-Bang-Deployment zu einem kontrollierten Übergang.

## Validierung gehört zur Migration

Ein erfolgreich ausgeführtes Migrationsskript bedeutet noch nicht, dass die Migration erfolgreich war.

Wir müssen die Daten überprüfen.

Zum Beispiel:

```sql
SELECT
    c.CustomerId,
    c.AddressText,
    ca.AddressLine1,
    ca.PostalCode,
    ca.City
FROM dbo.Customers AS c
LEFT JOIN dbo.CustomerAddresses AS ca
    ON ca.CustomerId = c.CustomerId;
```

In einem produktiven System sollte die Validierung unter anderem prüfen:

- fehlende Datensätze,
- unterschiedliche Werte,
- Duplikate,
- nicht migrierte Datensätze,
- Fehler beim Schreiben,
- und die Anzahl verbleibender Abhängigkeiten vom alten Modell.

Das Ziel ist nicht nur:

> Das Skript ist fertig.

Das Ziel lautet:

> Wir können nachweisen, dass das neue Modell korrekt funktioniert.

## Alte Abhängigkeiten erkennen

Bevor wir die alte Struktur entfernen, müssen wir außerdem wissen, ob sie noch verwendet wird.

Vielleicht wurde die Hauptanwendung bereits umgestellt.

Ein alter Report greift jedoch weiterhin auf `AddressText` zu.

Oder ein SQL-Agent-Job.

Oder ein SSIS-Paket.

Oder ein altes PowerShell-Skript.

Genau deshalb ist die Contract-Phase kein automatischer letzter Schritt.

Sie benötigt einen eigenen Freigabepunkt.

## Phase 3: Contract

Erst wenn:

- historische Daten vollständig migriert wurden,
- neue Schreibvorgänge korrekt verarbeitet werden,
- Anwendungen das neue Modell verwenden,
- die Validierung erfolgreich war,
- und alte Abhängigkeiten nicht mehr existieren,

beginnt die Contract-Phase.

Jetzt können wir:

- temporäre Synchronisierungslogik entfernen,
- alte Stored Procedures löschen,
- Compatibility Views entfernen,
- und schließlich die alte Spalte `AddressText` löschen.

Zum Beispiel:

```sql
ALTER TABLE dbo.Customers
DROP COLUMN AddressText;
```

Diese Anweisung ist jedoch der **letzte** Schritt.

Nicht der erste.

## Rollback oder Roll Forward?

Während der frühen Migrationsphase ist ein Rollback häufig noch relativ einfach.

Das alte Modell existiert weiterhin.

Die Anwendung kann gegebenenfalls zurückgeschaltet werden.

Nach der Contract-Phase sieht die Situation anders aus.

Wenn alte Strukturen entfernt wurden und bereits neue Daten nur noch im neuen Modell entstehen, kann ein vollständiger Rollback sehr teuer oder sogar riskanter als ein Roll Forward sein.

Deshalb sollte bereits vor der Migration definiert werden:

- bis zu welchem Punkt ein Rollback möglich ist,
- ab wann Roll Forward bevorzugt wird,
- welche Daten rekonstruiert werden müssten,
- und welche Validierung vor dem Contract notwendig ist.

## Wann ist Expand–Migrate–Contract sinnvoll?

Das Muster ist besonders hilfreich, wenn:

- mehrere Anwendungen dieselbe Datenbank verwenden,
- Deployments nicht gleichzeitig stattfinden können,
- Rückwärtskompatibilität benötigt wird,
- große Datenmengen migriert werden,
- das Wartungsfenster sehr klein ist,
- oder die Datenbank praktisch ohne Unterbrechung verfügbar bleiben muss.

## Der Preis des Musters

Expand–Migrate–Contract ist nicht kostenlos.

Während der Übergangsphase entstehen zusätzliche Elemente:

- zwei Datenmodelle,
- zusätzliche Migrationslogik,
- temporäre Stored Procedures,
- möglicherweise Dual Write,
- Validierungsabfragen,
- zusätzliches Monitoring.

Das System wird kurzfristig komplizierter.

Diese Komplexität ist jedoch bewusst und zeitlich begrenzt.

Dafür gewinnen wir Zeit und Kontrolle.

## Die wichtigste Aussage

> **Bei einer sicheren Schema-Evolution ist nicht nur der Zielzustand wichtig. Entscheidend ist ein kontrollierter Übergang vom alten zum neuen Datenmodell.**

Expand–Migrate–Contract macht genau diesen Übergang explizit:

**Expand → Migrate → Validate → Contract**

Statt einer riskanten Big-Bang-Migration erhalten wir mehrere kleine, überprüfbare Schritte.

Und genau darin liegt die Stärke dieses Musters.

## Nächster Schritt: Dual Write

Während der Migrate-Phase müssen häufig altes und neues Datenmodell gleichzeitig unterstützt werden.

Was passiert jedoch, wenn eine Geschäftsoperation in beide Modelle schreiben muss?

Was passiert, wenn der erste Schreibvorgang erfolgreich ist und der zweite fehlschlägt?

Genau darum geht es im nächsten Teil:

**Dual Write.**
