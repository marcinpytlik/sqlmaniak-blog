---
title: "Feature Flags bei Schemaänderungen: kontrollierte Umstellung auf ein neues Datenmodell"
date: 2026-09-23T00:01:00+02:00
slug: feature-flag-schema-change
description: "Feature Flags bei Schemamigrationen nutzen und Lese- sowie Schreibzugriffe schrittweise umstellen."
category: "Relationaler Renaissance"
tags: [SQL Server, feature flags, schema evolution, deployment, Datenmigration]
draft: false
---

# Feature Flags bei Schemaänderungen: kontrollierte Umstellung auf ein neues Datenmodell

Eine Schemaänderung und die Einführung einer Funktion müssen nicht gleichzeitig stattfinden.

Wir können zunächst eine neue Tabelle anlegen, Code bereitstellen und erst später das neue Modell für einen Teil des Verkehrs aktivieren. **Feature Flags** helfen dabei.

Eine Flag kann steuern:

- Lesen aus dem alten oder neuen Modell,
- Schreiben in eine oder zwei Strukturen,
- Aktivierung für ausgewählte Benutzer,
- schrittweise Erhöhung des Verkehrsanteils,
- schnelles Abschalten ohne erneutes Deployment.

> Eine Feature Flag trennt die Bereitstellung des Codes von der Aktivierung des neuen Verhaltens.

## Beispielszenario

Eine Anwendung migriert von `Customers.AddressText` zur Tabelle `CustomerAddresses`.

Wir definieren drei Flags:

```text
UseNewAddressRead
UseNewAddressWrite
EnableAddressV2
```

Jede steuert eine andere Phase.

## Getrennte Entscheidungen statt einer einzigen Flag

Eine einzige Flag `NewAddressModel` kann zu allgemein sein. Lesen und Schreiben bergen unterschiedliche Risiken.

Eine bessere Reihenfolge:

1. neue Schreibvorgänge im Hintergrund ausführen,
2. weiterhin aus dem alten Modell lesen,
3. Ergebnisse beider Lesewege vergleichen,
4. eine kleine Benutzergruppe umschalten,
5. den Anteil erhöhen,
6. alte Schreibvorgänge deaktivieren,
7. nach der Migration die Flags entfernen.

## Wo werden Flags gespeichert?

Mögliche Orte:

- Feature-Management-System,
- Anwendungskonfiguration,
- Datenbanktabelle,
- Umgebungsvariablen.

Einfache Tabelle:

```sql
CREATE TABLE config.FeatureFlags
(
    FeatureName  sysname NOT NULL,
    IsEnabled    bit NOT NULL,
    Percentage   tinyint NULL,
    UpdatedAt    datetime2(0) NOT NULL,
    UpdatedBy    sysname NOT NULL,

    CONSTRAINT PK_FeatureFlags
        PRIMARY KEY (FeatureName),

    CONSTRAINT CK_FeatureFlags_Percentage
        CHECK (Percentage BETWEEN 0 AND 100)
);
```

Die Anwendung sollte diese Tabelle nicht ohne Cache vor jeder Operation abfragen. Auch die Verzögerung bei der Verteilung von Änderungen ist zu berücksichtigen.

## Lese-Flag

Der Code kann die Datenquelle wählen:

```text
if UseNewAddressRead:
    read CustomerAddresses
else:
    read Customers.AddressText
```

In der Testphase ist ein **Shadow Read** oft besser:

1. der Benutzer erhält das Ergebnis aus dem alten Modell,
2. die Anwendung liest zusätzlich aus dem neuen Modell,
3. die Ergebnisse werden verglichen,
4. Unterschiede werden in der Telemetrie gespeichert.

Der Benutzer bemerkt nichts, während das Team Belege für die Kompatibilität sammelt.

## Schreib-Flag

Mögliche Modi:

```text
LegacyOnly
DualWrite
NewOnly
```

Das ist verständlicher als mehrere unabhängige boolesche Werte, die ungültige Kombinationen ergeben könnten.

Der Modus kann in der Datenbank gespeichert werden:

```sql
CREATE TABLE config.AddressWriteMode
(
    Mode varchar(20) NOT NULL,

    CONSTRAINT CK_AddressWriteMode
        CHECK (Mode IN ('LegacyOnly', 'DualWrite', 'NewOnly'))
);
```

Wichtig ist, dass sich der Modus nicht mitten in einer Transaktion ändert und alle Anwendungsinstanzen ihn gleich interpretieren.

## Schrittweise Einführung

Das neue Modell kann aktiviert werden für:

- Mitarbeiter,
- Test-Tenants,
- eine bestimmte Region,
- ausgewählte Kunden,
- einen festgelegten Verkehrsanteil.

Die Zuordnung muss stabil sein. Derselbe Kunde sollte nicht bei jeder Anfrage zufällig zwischen V1 und V2 wechseln.

Dazu kann ein Hash des Identifikators dienen:

```text
hash(CustomerId) % 100 < Percentage
```

So bleibt die Benutzergruppe bei einem bestimmten Prozentsatz stabil.

## Die Datenbank muss kompatibel bleiben

Eine Feature Flag ersetzt kein korrektes Schemadesign.

Soll das Abschalten der Flag den alten Weg wiederherstellen, muss das alte Modell weiterhin alle benötigten Daten enthalten. Sobald Informationen gespeichert wurden, die nur V2 darstellen kann, ist eine Rückkehr möglicherweise unmöglich.

Die Flag kann Code abschalten, aber keine Datenänderungen automatisch rückgängig machen.

## Monitoring

Jede Aktivierung muss mit Metriken verknüpft werden:

- Anzahl der V1- und V2-Operationen,
- Fehler je Pfad,
- Unterschiede bei Shadow Reads,
- Antwortzeiten,
- inkonsistente Datensätze,
- Deadlocks und Blocking,
- Warteschlange ausstehender Migrationen,
- Nutzung des alten Modells.

Beispieltabelle für Abweichungen:

```sql
CREATE TABLE audit.AddressReadDifferences
(
    DifferenceId bigint IDENTITY(1,1) NOT NULL,
    CustomerId   int NOT NULL,
    LegacyValue  nvarchar(500) NULL,
    NewValue     nvarchar(500) NULL,
    DetectedAt   datetime2(0) NOT NULL,

    CONSTRAINT PK_AddressReadDifferences
        PRIMARY KEY (DifferenceId)
);
```

## Notabschaltung

Die Flag sollte den neuen Weg schnell deaktivieren können. Es muss jedoch klar sein, was das bedeutet:

- nur Lesezugriffe kehren zu V1 zurück,
- Schreibvorgänge gehen weiter nach V2,
- beide Richtungen werden gestoppt,
- die Warteschlange muss geleert werden,
- V2-Daten müssen zurücksynchronisiert werden.

Ohne Definition kann ein Kill Switch noch größere Inkonsistenzen erzeugen.

## Technische Schulden durch Flags

Temporäre Flags müssen entfernt werden.

Jede zurückgelassene Flag:

- erhöht die Zahl der Codepfade,
- erschwert Tests,
- verkompliziert die Fehlersuche,
- ermöglicht unerwartete Kombinationen.

Für jede Flag sollten dokumentiert sein:

- Verantwortlicher,
- Zweck,
- Erstellungsdatum,
- Bedingung für die Entfernung,
- maximale Lebensdauer.

## Wann einsetzen?

Feature Flags eignen sich, wenn:

- der Verkehrsanteil schrittweise erhöht werden soll,
- neuer Code zunächst inaktiv bereitgestellt werden kann,
- eine schnelle Deaktivierung nötig ist,
- Shadow Reads geplant sind,
- die Migration mehrere Anwendungsinstanzen umfasst.

## Wann ist Vorsicht nötig?

- das alte Modell kann neue Daten nicht darstellen,
- Schreibvorgänge sind auf mehrere Systeme verteilt,
- Flags werden inkonsistent verbreitet,
- vergleichendes Monitoring fehlt,
- Flags werden nach der Migration nicht entfernt.

## Zusammenfassung

Feature Flags steuern das Tempo der Umstellung auf ein neues Schema. Die Grundregeln bleiben bestehen:

- das Schema muss kompatibel sein,
- Daten müssen migriert werden,
- Schreibvorgänge müssen konsistent bleiben,
- Ergebnisse müssen verglichen werden,
- das alte Modell muss schließlich entfernt werden.

Eine Flag ist kein Migrationsplan, sondern ein Werkzeug, um diesen Plan schrittweise und ohne erneutes Deployment umzusetzen.
