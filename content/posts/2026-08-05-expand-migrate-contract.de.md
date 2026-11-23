---
title: "Expand–Migrate–Contract: Schemaänderungen ohne Anwendungsstillstand"
date: 2026-08-05T00:01:00+02:00
slug: "expand-migrate-contract-ewolucja-schematu"
description: "Ein praktisches Muster zur sicheren SQL-Server-Schemaentwicklung: Modell erweitern, Daten migrieren, Kompatibilität sichern, validieren und alte Strukturen entfernen."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - projektowanie baz danych
  - ewolucja schematu
  - deployment
  - migracja danych
draft: false
---

# Expand–Migrate–Contract: Schemaänderungen ohne Anwendungsstillstand

Eine neue Tabelle zu entwerfen ist relativ einfach. Eine Tabelle zu ändern, die bereits von Anwendungen, Berichten, ETL-Prozessen und Benutzern verwendet wird, ist deutlich schwieriger.

Im Labor können wir `ALTER TABLE` ausführen, den Code anpassen und alles neu starten. In Produktion laufen jedoch möglicherweise zwei Anwendungsversionen eine Zeit lang parallel. Ein Bericht erwartet noch die alte Spalte, während eine Integration nur einmal täglich läuft und einen Fehler erst Stunden nach dem Deployment offenlegt.

Das Muster **Expand–Migrate–Contract** teilt eine Änderung in kontrollierte Phasen:

1. **Expand** — neue Struktur hinzufügen, ohne die alte zu entfernen.
2. **Migrate** — Daten und Anwendungszugriffe umstellen.
3. **Validate** — Vollständigkeit und tatsächliche Nutzung des alten Modells prüfen.
4. **Contract** — erst dann die alte Struktur entfernen.

Der wichtigste Grundsatz:

> Eine Schemaänderung ist ein Deployment-Prozess und keine einzelne DDL-Anweisung.

## Beispielproblem

Angenommen, die erste Systemversion speichert die Kundenadresse in einer einzigen Spalte:

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

Später möchte das Unternehmen:

- mehrere Adressen speichern,
- Rechnungs- und Lieferadressen unterscheiden,
- Kunden nach Stadt filtern,
- Daten mit einem Kurierdienst integrieren.

Eine eigene Adresstabelle ist ein natürliches Zielmodell. `AddressText` sofort zu entfernen, wäre jedoch riskant.

## Phase 1: Expand

Zunächst legen wir die neue Tabelle an:

```sql
CREATE TABLE dbo.CustomerAddresses
(
    CustomerAddressId bigint IDENTITY(1,1) NOT NULL,
    CustomerId        int NOT NULL,
    AddressType       varchar(20) NOT NULL,
    AddressLine1      nvarchar(200) NOT NULL,
    PostalCode        nvarchar(20) NULL,
    City              nvarchar(100) NULL,
    CountryCode       char(2) NOT NULL,
    IsPrimary         bit NOT NULL,

    CONSTRAINT PK_CustomerAddresses
        PRIMARY KEY (CustomerAddressId),

    CONSTRAINT FK_CustomerAddresses_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customers(CustomerId)
);
```

Die alte Spalte bleibt erhalten. Anwendung V1 kann unverändert weiterlaufen, während V2 für das neue Modell vorbereitet wird.

Eine erweiternde Änderung lässt sich meist leichter bereitstellen als eine destruktive. Eine zusätzliche Tabelle verletzt den bestehenden Vertrag nicht; das Entfernen einer Spalte dagegen schon.

## Phase 2: Migrate

Die Daten müssen in das neue Modell übertragen werden. Bei kleinen Tabellen reicht ein `INSERT ... SELECT`; bei großen Tabellen sollten wir in Batches arbeiten.

```sql
WHILE 1 = 1
BEGIN
    ;WITH Batch AS
    (
        SELECT TOP (1000)
            c.CustomerId,
            c.AddressText
        FROM dbo.Customers AS c
        WHERE c.AddressText IS NOT NULL
          AND NOT EXISTS
          (
              SELECT 1
              FROM dbo.CustomerAddresses AS ca
              WHERE ca.CustomerId = c.CustomerId
          )
        ORDER BY c.CustomerId
    )
    INSERT INTO dbo.CustomerAddresses
    (
        CustomerId,
        AddressType,
        AddressLine1,
        CountryCode,
        IsPrimary
    )
    SELECT
        CustomerId,
        'Other',
        AddressText,
        'PL',
        1
    FROM Batch;

    IF @@ROWCOUNT = 0
        BREAK;
END;
```

Die Migration in Batches reduziert:

- die Dauer einzelner Transaktionen,
- das Wachstum des Transaktionslogs,
- die Dauer von Sperren,
- das Risiko eines langwierigen Rollbacks,
- die Auswirkungen auf den laufenden Betrieb.

Der Prozess sollte idempotent oder zumindest wiederaufnehmbar sein. Ein Neustart darf keine Duplikate erzeugen.

## Kompatibilitätsphase

Alte und neue Anwendungsversionen können vorübergehend parallel laufen. Dann muss festgelegt werden, wie die Konsistenz erhalten bleibt.

Mögliche Lösungen:

- temporäres Dual Write,
- eine Stored Procedure, die beide Modelle beschreibt,
- eine Kompatibilitätsview,
- V1-Schreibzugriffe abschalten, sobald alle Anwendungsinstanzen umgestellt sind.

Dual Write ist nützlich, erhöht aber die Komplexität. Gelingt ein Schreibvorgang und der andere nicht, entstehen Inkonsistenzen. Beide Schreibvorgänge sollten deshalb Teil einer lokalen Transaktion sein.

## Validierung vor dem Entfernen des alten Modells

Entferne eine Spalte nicht nur deshalb, weil die neue Anwendung bereitgestellt wurde. Du brauchst Nachweise.

Eine einfache Vollständigkeitsprüfung:

```sql
SELECT
    c.CustomerId,
    c.CustomerName,
    c.AddressText
FROM dbo.Customers AS c
WHERE c.AddressText IS NOT NULL
  AND NOT EXISTS
  (
      SELECT 1
      FROM dbo.CustomerAddresses AS ca
      WHERE ca.CustomerId = c.CustomerId
  );
```

Die Abfrage sollte null Zeilen liefern.

Prüfe auch die Modulabhängigkeiten:

```sql
SELECT
    ReferencingSchema = OBJECT_SCHEMA_NAME(d.referencing_id),
    ReferencingObject = OBJECT_NAME(d.referencing_id),
    d.referenced_entity_name
FROM sys.sql_expression_dependencies AS d
WHERE d.referenced_id = OBJECT_ID(N'dbo.Customers');
```

Das bietet noch keine vollständige Garantie. Dynamisches SQL, Anwendungscode und externe Berichte erscheinen möglicherweise nicht in den Metadaten. Nutze zusätzlich Query Store, Extended Events, Monitoring von Anwendungsfehlern und die Analyse von Code-Repositories.

## Phase 3: Contract

Erst wenn die Migration abgeschlossen und Anwendung V1 außer Betrieb ist, entfernen wir die alte Struktur:

```sql
ALTER TABLE dbo.Customers
    DROP COLUMN AddressText;
```

Vorher müssen folgende Komponenten entfernt oder angepasst werden:

- Stored Procedures mit Verweisen auf die Spalte,
- Kompatibilitätsviews,
- Trigger,
- Indizes,
- Berichte,
- ETL-Prozesse,
- ORM-Mappings.

Die `Contract`-Phase sollte ein separates Deployment sein. Die Trennung von `Expand` schafft Zeit, das System zu beobachten und Anwendungscode sicher zurückzurollen.

## Rollback oder Roll Forward?

Ein Code-Rollback bedeutet nicht zwangsläufig, dass sich eine Datenbankmigration zurücknehmen lässt. Wenn die neue Anwendung Daten geschrieben hat, die das alte Modell nicht darstellen kann, droht beim Zurückwechseln Informationsverlust.

Lege vorher fest:

- bis zu welchem Zeitpunkt ein Rollback möglich ist,
- wann eine Roll-forward-Strategie gilt,
- wie Daten nach einer unvollständigen Migration wiederhergestellt werden,
- welche Metriken einen Deployment-Stopp auslösen.

## Wann sollte man das Muster verwenden?

Expand–Migrate–Contract eignet sich besonders, wenn:

- das Deployment keine langen Ausfallzeiten verursachen darf,
- die Anwendung auf mehreren Instanzen läuft,
- Berichte und Integrationen dasselbe Schema nutzen,
- die Datenmigration lange dauert,
- eine kontrollierte Umschaltung erforderlich ist.

## Kosten

Das Muster ist nicht kostenlos. Vorübergehend müssen zwei Modelle, zusätzlicher Kompatibilitätscode und mehr Deployment-Schritte gepflegt werden. Auch Monitoring und Aufräumarbeiten sind notwendig.

Das sind die Kosten einer kontrollierten Änderung. Die Alternative ist ein Big-Bang-Deployment, bei dem jeder unerkannte Nutzer der alten Struktur das System zum Stillstand bringen kann.

## Zusammenfassung

Ausgereifte Schemaentwicklung beginnt nicht mit der Frage:

> Wird die `ALTER TABLE`-Anweisung ausgeführt?

Sondern mit:

- Bleibt das System während der Änderung verfügbar?
- Bleiben beide Anwendungsversionen kompatibel?
- Kann die Migration fortgesetzt werden?
- Wie bestätigen wir die Vollständigkeit der Daten?
- Wann lässt sich das alte Modell sicher entfernen?

Expand–Migrate–Contract verwandelt eine riskante Änderung in eine Folge kleiner, beobachtbarer und umkehrbarer Schritte. Deshalb gehört es zu den grundlegenden Mustern der Evolution relationaler Datenbanken.
