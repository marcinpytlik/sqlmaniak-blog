---
title: "Shadow Column: Den Datentyp einer Spalte in SQL Server sicher ändern"
date: 2026-08-19T00:01:00+02:00
slug: "shadow-column-datentyp-sicher-aendern"
description: "Wie man den Typ oder die Bedeutung einer Spalte ändert, ohne ein riskantes ALTER COLUMN auf einer großen Tabelle auszuführen."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - Shadow Column
  - ALTER TABLE
  - Datenmigration
  - Zero Downtime
draft: false
---

# Shadow Column: Den Datentyp einer Spalte in SQL Server sicher ändern

Eine Änderung des Spaltentyps sieht nach einer einfachen Operation aus:

```sql
ALTER TABLE dbo.Documents
ALTER COLUMN DocumentNumber varchar(30) NOT NULL;
```

Bei einer kleinen Tabelle kann sie schnell abgeschlossen sein. Bei einer großen Produktionstabelle kann sie jedoch bedeuten:

- eine lange Schema-Modification-Sperre,
- Umschreiben der Daten,
- Wachstum des Transaktionslogs,
- Neuaufbau von Indizes,
- Konflikte mit laufenden Abfragen,
- Probleme mit Anwendungen, die den alten Typ erwarten.

Das Muster **Shadow Column** ermöglicht eine schrittweise Änderung. Anstatt die bestehende Spalte zu verändern, fügen wir daneben eine neue hinzu.

> Shadow Column verwandelt eine große Änderung in mehrere kleine, kontrollierte Schritte.

## Szenario

Die erste Systemversion speichert eine Dokumentnummer als `int`:

```sql
CREATE TABLE dbo.Documents
(
    DocumentId     bigint IDENTITY(1,1) NOT NULL,
    DocumentNumber int NOT NULL,

    CONSTRAINT PK_Documents
        PRIMARY KEY (DocumentId)
);
```

Nach einigen Jahren soll die Dokumentnummer ein Präfix wie `FV/2026/1001` enthalten. Dafür reicht `int` nicht mehr aus.

## Phase 1: Shadow Column hinzufügen

```sql
ALTER TABLE dbo.Documents
ADD DocumentNumberV2 varchar(30) NULL;
```

Die neue Spalte erlaubt zunächst `NULL`. Dadurch müssen beim Hinzufügen nicht sofort alle Datensätze aktualisiert werden.

Die alte Anwendung verwendet weiterhin `DocumentNumber`, während die neue auf `DocumentNumberV2` vorbereitet werden kann.

## Phase 2: Backfill

Historische Daten werden in Batches migriert:

```sql
WHILE 1 = 1
BEGIN
    UPDATE TOP (5000) dbo.Documents
    SET DocumentNumberV2 =
        CONVERT(varchar(30), DocumentNumber)
    WHERE DocumentNumberV2 IS NULL;

    IF @@ROWCOUNT = 0
        BREAK;

    WAITFOR DELAY '00:00:00.200';
END;
```

Eine kurze Pause zwischen den Batches ist nicht immer nötig, kann aber Log, I/O und Sperren entlasten.

Den Fortschritt überwachen wir mit:

```sql
SELECT
    TotalRows = COUNT_BIG(*),
    MigratedRows = COUNT_BIG(DocumentNumberV2),
    MissingRows = SUM(
        CASE WHEN DocumentNumberV2 IS NULL
             THEN 1 ELSE 0 END
    )
FROM dbo.Documents;
```

## Phase 3: In beide Spalten schreiben

In der Übergangszeit kann eine Stored Procedure beide Werte pflegen:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Document_Create
    @DocumentNumberV2 varchar(30)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @LegacyNumber int =
        TRY_CONVERT(int, @DocumentNumberV2);

    INSERT INTO dbo.Documents
    (
        DocumentNumber,
        DocumentNumberV2
    )
    VALUES
    (
        @LegacyNumber,
        @DocumentNumberV2
    );
END;
```

Das Beispiel zeigt ein wichtiges Problem: Das neue Format lässt sich nicht immer auf das alte abbilden. Die Nummer `FV/2026/1001` kann semantisch nicht als `int` dargestellt werden.

Vollständiges Dual Write ist daher nur möglich, solange keine Werte verwendet werden, die das alte Modell nicht unterstützt. Der Wechsel sollte ein bewusst geplanter Cutover sein.

**Hinweis für Produktion:** Die Beispielprozedur fügt einen möglicherweise nullwertigen `@LegacyNumber` in eine `NOT NULL`-Spalte ein. Bei einer formatierten Nummer schlägt das INSERT fehl. Das Beispiel zeigt eine Kompatibilitätsgrenze und ist keine produktionsreife Lösung.

## Phase 4: Lesezugriffe umstellen

Die neue Anwendung beginnt, `DocumentNumberV2` zu lesen.

Während der Übergangszeit ist möglich:

```sql
SELECT
    DocumentId,
    EffectiveDocumentNumber =
        COALESCE(
            DocumentNumberV2,
            CONVERT(varchar(30), DocumentNumber)
        )
FROM dbo.Documents;
```

Häufig ist eine Compatibility View oder Stored Procedure besser, die die Migrationsdetails vor der Anwendung verbirgt.

## Indizes und Constraints

War die alte Spalte indiziert, benötigt meist auch die neue einen Index:

```sql
CREATE UNIQUE INDEX UX_Documents_DocumentNumberV2
ON dbo.Documents(DocumentNumberV2)
WHERE DocumentNumberV2 IS NOT NULL;
```

Ein gefilterter Index erzwingt die Eindeutigkeit von Nicht-NULL-Werten schon vor Abschluss der Migration.

Anschließend auf Duplikate prüfen:

```sql
SELECT
    DocumentNumberV2,
    COUNT_BIG(*) AS DuplicateCount
FROM dbo.Documents
GROUP BY DocumentNumberV2
HAVING COUNT_BIG(*) > 1;
```

Erst bei leerem Ergebnis kann die vollständige Eindeutigkeit sicher durchgesetzt werden.

## Phase 5: Das Schema verschärfen

Nach der Migration:

```sql
ALTER TABLE dbo.Documents
ALTER COLUMN DocumentNumberV2 varchar(30) NOT NULL;
```

Auch diese Operation verlangt Vorsicht. Vorher müssen alle `NULL`-Werte ausgeschlossen und mögliche Sperren bewertet werden. Je nach Tabellengröße und SQL-Server-Version empfiehlt sich ein Test mit repräsentativer Datenmenge.

## Phase 6: Alte Spalte entfernen

Nachdem die alte Anwendung und ihre Abhängigkeiten außer Betrieb sind:

```sql
ALTER TABLE dbo.Documents
DROP COLUMN DocumentNumber;
```

Danach kann die neue Spalte umbenannt werden. Das ist aber nicht immer sinnvoll: Eine Umbenennung verändert den Vertrag erneut. Manchmal ist es sicherer, `DocumentNumberV2` beizubehalten und die Bereinigung später separat durchzuführen.

## Synchronisation durch Trigger

Manchmal kopiert ein Trigger Werte zwischen den Spalten. Als Übergangslösung kann das schnell sein, bringt jedoch Nachteile:

- verborgene Schreiblogik,
- kompliziertere Mehrzeilenoperationen,
- höhere Kosten jeder Änderung,
- mögliche Rekursion und schwer erkennbare Fehler,
- übersehene Abhängigkeiten bei der Anwendungsanalyse.

Lässt sich die Logik in einer Stored Procedure oder Anwendungsschicht unterbringen, ist sie meist besser beobachtbar.

## Wann ist das Muster besonders nützlich?

Shadow Column eignet sich für:

- Datentypänderungen,
- Änderungen der Einheit, etwa Cent in Dezimalbeträge,
- neue Kodierungen von Werten,
- Aufteilung eines Werts auf mehrere Spalten,
- Einführung verschlüsselter Datenrepräsentationen,
- Migration alter Identifikatoren.

## Kosten und Risiken

Während der Migration wird die Tabelle breiter und Schreibvorgänge können teurer werden. Beide Spalten müssen konsistent bleiben; die Bereinigung muss abgeschlossen werden.

Der größte Fehler ist, die Shadow Column dauerhaft bestehen zu lassen. Dann weiß das Team irgendwann nicht mehr, welche Version maßgeblich ist.

## Zusammenfassung

`ALTER COLUMN` ist eine technische Operation. Die Änderung eines Datenvertrags ist ein architektonischer Prozess.

Shadow Column verschafft Zeit für Datenmigration, Deployment des neuen Codes, Wertevergleich, Indexvorbereitung und Ablösung des alten Modells.

Statt einer einzigen riskanten Änderung entsteht ein sicherer Übergang von der alten Bedeutung einer Spalte zur neuen.
