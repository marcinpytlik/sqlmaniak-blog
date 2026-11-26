---
title: "Dual Write in Datenbanken: hilfreiche Brücke oder Quelle von Inkonsistenzen?"
date: 2026-08-11T00:01:00+02:00
slug: "dual-write-baza-danych"
description: "Altes und neues Datenmodell während einer SQL-Server-Schemamigration sicher parallel beschreiben."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - dual write
  - migracja danych
  - transakcje
  - spójność danych
draft: false
---

# Dual Write in Datenbanken: hilfreiche Brücke oder Quelle von Inkonsistenzen?

Bei der Schemaentwicklung gibt es häufig eine Phase, in der alte und neue Strukturen parallel existieren müssen. Anwendung V1 schreibt in die alte Tabelle, während Anwendung V2 bereits das neue Modell erwartet.

Eine Lösung ist **Dual Write**: dieselbe Geschäftsoperation wird an zwei Stellen geschrieben.

Das Muster klingt einfach:

1. Daten in das alte Modell schreiben.
2. Daten in das neue Modell schreiben.
3. Beide Modelle bis zum Abschluss der Migration pflegen.

Das Hauptproblem: Zwei Schreibvorgänge schaffen zwei mögliche Fehlerstellen.

> Dual Write ist kein Problem, wenn beide Schreibvorgänge atomar sind. Problematisch wird es, wenn einer erfolgreich sein kann und der andere fehlschlägt.

## Beispiel: Adressmigration

Das alte Modell speichert Adressen in `Customers.AddressText`. Das neue Modell verwendet `CustomerAddresses`.

Eine temporäre Prozedur kann beide Modelle aktualisieren:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_CustomerAddress_Save
    @CustomerId   int,
    @AddressLine1 nvarchar(200),
    @PostalCode   nvarchar(20),
    @City         nvarchar(100)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRANSACTION;

    UPDATE dbo.Customers
    SET AddressText = CONCAT(
        @AddressLine1,
        N', ',
        @PostalCode,
        N' ',
        @City
    )
    WHERE CustomerId = @CustomerId;

    MERGE dbo.CustomerAddresses AS target
    USING
    (
        SELECT
            @CustomerId AS CustomerId,
            @AddressLine1 AS AddressLine1,
            @PostalCode AS PostalCode,
            @City AS City
    ) AS source
        ON target.CustomerId = source.CustomerId
       AND target.IsPrimary = 1
    WHEN MATCHED THEN
        UPDATE SET
            AddressLine1 = source.AddressLine1,
            PostalCode = source.PostalCode,
            City = source.City
    WHEN NOT MATCHED THEN
        INSERT
        (
            CustomerId,
            AddressType,
            AddressLine1,
            PostalCode,
            City,
            IsPrimary
        )
        VALUES
        (
            source.CustomerId,
            'Other',
            source.AddressLine1,
            source.PostalCode,
            source.City,
            1
        );

    COMMIT;
END;
```

Beide Schreibvorgänge liegen in einer SQL-Server-Transaktion. Schlägt der zweite fehl, wird auch der erste zurückgerollt.

In der Praxis bevorzugen viele Teams explizite `UPDATE`- und `INSERT`-Anweisungen gegenüber `MERGE`, weil sich Nebenläufigkeit und komplexe Sonderfälle besser kontrollieren lassen.

## Schlechtester Fall: zwei unabhängige Aufrufe

Gefährlicher Anwendungscode kann zunächst logisch erscheinen:

```text
UPDATE starego modelu
COMMIT

INSERT do nowego modelu
COMMIT
```

Wenn der erste Schritt gelingt und der zweite fehlschlägt, unterscheiden sich die Modelle. Ein erneuter Versuch kann den ersten Schreibvorgang ein zweites Mal ausführen.

Noch schwieriger wird es, wenn ein Schreibvorgang SQL Server betrifft und der andere einen externen Dienst oder Message Broker. Dann gibt es keine einzelne lokale Transaktion für beide Ressourcen.

Bessere Lösungen können sein:

- Transactional Outbox.
- Eine Änderungswarteschlange.
- Change Data Capture.
- Ein asynchroner Synchronisierungsprozess.
- Eine einzige verbindliche Datenquelle.

## Welches Modell ist die Quelle der Wahrheit?

Dual Write benötigt eine klar definierte Richtung.

### Das alte Modell ist maßgeblich

Die neue Struktur wird nachgelagert aktualisiert. Das kann am Anfang der Migration sicherer sein, wenn der meiste Traffic noch V1 verwendet.

### Das neue Modell ist maßgeblich

Die alte Struktur bleibt nur für Legacy-Berichte oder V1-Anwendungen bestehen. Das ist ein natürlicher Schritt vor ihrer Entfernung.

### Beide Modelle sind gleichberechtigt

Das ist die riskanteste Variante. Wenn beide unabhängig bearbeitet werden können, sind Regeln zur Konfliktlösung erforderlich. Statt einer kontrollierten Migration entstehen möglicherweise zwei führende Datenquellen.

## Konsistenzprüfung

Während Dual Write müssen die Modelle regelmäßig verglichen werden:

```sql
SELECT
    c.CustomerId,
    LegacyAddress = c.AddressText,
    NewAddress = CONCAT(
        ca.AddressLine1,
        N', ',
        ca.PostalCode,
        N' ',
        ca.City
    )
FROM dbo.Customers AS c
JOIN dbo.CustomerAddresses AS ca
    ON ca.CustomerId = c.CustomerId
   AND ca.IsPrimary = 1
WHERE ISNULL(c.AddressText, N'')
   <> ISNULL(
        CONCAT(
            ca.AddressLine1,
            N', ',
            ca.PostalCode,
            N' ',
            ca.City
        ),
        N''
   );
```

Dieser Konsistenzbericht gehört zum Migrationsmonitoring und nicht nur zu einem einmaligen Test.

Sinnvolle Messwerte sind:

- Anzahl inkonsistenter Datensätze.
- Zeit seit der letzten Synchronisierung.
- Anzahl der Schreibfehler pro Modell.
- Anzahl der Wiederholungen.
- Anteil des Traffics über V1 und V2.

## Idempotenz

Operationen während der Migration müssen Wiederholungen vertragen. Dabei helfen:

- Eindeutige Geschäftsschlüssel.
- `IdempotencyKey`.
- Kontrolliert implementiertes `UPSERT`.
- Eine Tabelle verarbeiteter Nachrichten.
- Speicherung der Datensatzversion.
- Explizite Operationskennungen.

Beispiel einer Operationstabelle:

```sql
CREATE TABLE dbo.ProcessedRequests
(
    RequestId uniqueidentifier NOT NULL,
    ProcessedAt datetime2(0) NOT NULL,
    ResultCode varchar(30) NOT NULL,

    CONSTRAINT PK_ProcessedRequests
        PRIMARY KEY (RequestId)
);
```

Vor dem Schreiben kann die Anwendung oder Prozedur prüfen, ob die Anforderung bereits verarbeitet wurde.

## Wie lange sollte Dual Write bleiben?

So kurz wie möglich.

Dual Write ist eine Übergangslösung. Je länger sie läuft, desto eher wird sie zum dauerhaften Architekturbaustein. Jede Änderung muss dann zwei Modelle berücksichtigen, und das Team verliert die Sicherheit, welches Modell maßgeblich ist.

Definiere vor dem Rollout klare Abschaltbedingungen:

- Alle Anwendungsinstanzen laufen mit V2.
- Die Migration historischer Daten ist abgeschlossen.
- Der Konsistenzbericht zeigt über einen vereinbarten Zeitraum keine Unterschiede.
- Legacy-Berichte und Integrationen sind umgestellt.
- Das Monitoring bestätigt, dass niemand mehr das alte Modell verwendet.

## Wann einsetzen?

Dual Write kann geeignet sein, wenn:

- Beide Schreibvorgänge in derselben Datenbanktransaktion stattfinden.
- Die Übergangszeit kurz ist.
- Ein Cutover ohne Ausfallzeit nötig ist.
- Ein Vergleichsbericht beide Modelle kontrolliert.
- Die maßgebliche Datenquelle eindeutig feststeht.

## Wann vermeiden?

Besondere Vorsicht ist nötig, wenn:

- Schreibvorgänge verschiedene Systeme betreffen.
- Atomarität nicht garantiert werden kann.
- Beide Modelle unabhängig bearbeitet werden können.
- Wiederholungs- und Idempotenzmechanismen fehlen.
- Niemand ein Abschaltdatum festgelegt hat.

## Zusammenfassung

Dual Write ist eine nützliche Brücke bei der Schemaentwicklung. Es ist jedoch keine harmlose Anweisung, „zweimal zu schreiben“.

Sicheres Dual Write benötigt:

- Atomarität.
- Eine maßgebliche Datenquelle.
- Idempotenz.
- Monitoring von Inkonsistenzen.
- Eine kurze Laufzeit.
- Einen klaren Abschaltplan.

Die wichtigste Frage lautet nicht:

> Können wir an zwei Stellen schreiben?

Sondern:

> Was tun wir, wenn einer der Schreibvorgänge fehlschlägt?
