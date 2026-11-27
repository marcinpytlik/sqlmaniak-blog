---
title: "Compatibility View: Das Datenmodell ändern, ohne alte Berichte zu beschädigen"
date: 2026-09-02T00:01:00+02:00
slug: "compatibility-view-alte-berichte"
description: "Ein Kompatibilitäts-View als Übergangsschicht zwischen dem alten Datenvertrag und dem neuen SQL-Server-Modell."
category: "Relationale Renaissance"
tags: [SQL Server, Views, Kompatibilität, Berichte, Schemamigration]
draft: false
---

# Compatibility View: Das Datenmodell ändern, ohne alte Berichte zu beschädigen

Eine Änderung des Datenmodells endet nicht bei der Anwendung. Tabellen werden außerdem verwendet von:

- Berichten,
- ETL-Prozessen,
- Integrationen,
- Tabellenkalkulationen der Benutzer,
- Ad-hoc-Abfragen,
- Systemen, die das Datenbankteam möglicherweise gar nicht kennt.

Das Muster **Compatibility View** stellt das neue Modell in dem Format bereit, das bestehende Verbraucher erwarten.

> Ein Kompatibilitäts-View trennt die physische Datenstruktur vom vorübergehend weiter benötigten Datenvertrag.

## Szenario

Die alte Kundentabelle enthielt:

```sql
dbo.Customers
(
    CustomerId,
    CustomerName,
    AddressText
)
```

Nach der Normalisierung liegen die Adressen in `CustomerAddresses`.

Der alte Bericht führt weiterhin aus:

```sql
SELECT
    CustomerId,
    CustomerName,
    AddressText
FROM dbo.Customers;
```

Das sofortige Entfernen der Spalte würde den Bericht beschädigen.

## Kompatibilitäts-View

Wir können einen View erstellen, der das alte Format rekonstruiert:

```sql
CREATE OR ALTER VIEW dbo.vw_Customers_Legacy
AS
    SELECT
        c.CustomerId,
        c.CustomerName,
        AddressText =
            CONCAT(
                ca.AddressLine1,
                CASE
                    WHEN ca.PostalCode IS NOT NULL
                      OR ca.City IS NOT NULL
                    THEN N', '
                    ELSE N''
                END,
                COALESCE(ca.PostalCode + N' ', N''),
                COALESCE(ca.City, N'')
            )
    FROM dbo.Customers AS c
    OUTER APPLY
    (
        SELECT TOP (1)
            a.AddressLine1,
            a.PostalCode,
            a.City
        FROM dbo.CustomerAddresses AS a
        WHERE a.CustomerId = c.CustomerId
        ORDER BY
            a.IsPrimary DESC,
            a.CustomerAddressId
    ) AS ca;
```

Der Bericht kann von der Tabelle auf den View umgestellt werden, ohne das neue Modell kennen zu müssen.

## Alten Objektnamen beibehalten

Manchmal wird eine aggressivere Variante eingesetzt:

1. Alte Tabelle umbenennen.
2. Unter dem alten Namen einen View erstellen.
3. Das neue Modell in anderen Tabellen speichern.

Konzeptionelles Beispiel:

```sql
EXEC sys.sp_rename
    N'dbo.Customers',
    N'Customers_Internal';

CREATE VIEW dbo.Customers
AS
SELECT ...
```

Damit lassen sich Änderungen bei den Verbrauchern reduzieren. Allerdings sind gründliche Tests nötig. Anwendungen können eine Tabelle erwarten, Schreiboperationen ausführen, Hints verwenden oder von bestimmten Metadaten abhängen.

`sp_rename` aktualisiert nicht automatisch alle textuellen Referenzen.

## Nur lesbar oder auch beschreibbar?

Am sichersten ist ein schreibgeschützter Compatibility View.

Einfache Views sind manchmal automatisch aktualisierbar. Bei komplexen Zuordnungen kann ein `INSTEAD OF TRIGGER` verwendet werden, der jedoch verborgene Komplexität schafft.

```sql
CREATE OR ALTER TRIGGER dbo.tr_CustomersLegacy_Update
ON dbo.vw_Customers_Legacy
INSTEAD OF UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Jawne przepisanie starego kontraktu
    -- na operacje w nowym modelu.
END;
```

Der Trigger muss Mehrzeilenoperationen, Fehler, Transaktionen und Parallelität korrekt behandeln. Deshalb sollte er eine Übergangslösung und keine dauerhafte Datenbank-API sein.

## Stabiler Vertrag

Der View muss genau abbilden:

- Spaltennamen,
- Datentypen,
- Bedeutung der Werte,
- Behandlung von `NULL`,
- Zeilenzahlen,
- Regeln für die Datenauswahl.

Speichert das neue Modell mehrere Adressen, der alte Vertrag aber nur eine, muss festgelegt werden, welche zurückgegeben wird. Meist ist es die Hauptadresse, aber die Entscheidung muss explizit sein.

Ohne diese Regel können doppelte Kundenzeilen entstehen und Berichtsergebnisse verändert werden.

## Performance

Ein normaler View speichert keine Daten. Jede Abfrage führt seine Definition aus.

Las ein Bericht früher nur eine Tabelle und verbindet der View jetzt mehrere große Tabellen, kann sich die Performance verschlechtern.

Prüfe:

- Ausführungsplan,
- Indizes auf Join-Schlüsseln,
- Selektivität der Filter,
- Zeilenzahl nach dem Join,
- Funktionen und Typkonvertierungen,
- Verhalten der Berichtsparameter.

Beispielindex:

```sql
CREATE INDEX IX_CustomerAddresses_Customer_Primary
ON dbo.CustomerAddresses
(
    CustomerId,
    IsPrimary
)
INCLUDE
(
    AddressLine1,
    PostalCode,
    City
);
```

## Versionierung der Views

Statt eines einzigen „Legacy“-Objekts können Verträge explizit versioniert werden:

```text
reporting.vw_Customers_v1
reporting.vw_Customers_v2
```

Das schafft Transparenz. Verbraucher kennen ihre Version und das Team kann V1 gezielt ablösen.

Dokumentiere:

- Verantwortliche für jeden Verbraucher,
- geplantes Migrationsdatum,
- Abschaltdatum des alten Views,
- Überwachung der Nutzung.

## Wie erkennen wir, ob der View noch verwendet wird?

SQL Server speichert keine vollständige Historie aller Verbraucher. Helfen können:

- Query Store,
- Extended Events,
- Plan-Cache-Analyse,
- Berichtslogs,
- Quellcode-Repositories,
- Query Auditing,
- Fehlerüberwachung nach kontrollierter Abschaltung in einer Testumgebung.

Ein Compatibility View ohne Verantwortlichen und Enddatum bleibt wahrscheinlich für immer.

## Wann einsetzen?

Compatibility View ist sinnvoll, wenn:

- das physische Modell geändert wird, das alte Leseformat aber weiter benötigt wird,
- Berichte langsamer migriert werden als die Anwendung,
- eine kontrollierte Übergangszeit nötig ist,
- die Zuordnung zwischen altem und neuem Vertrag eindeutig ist.

## Wann nicht einsetzen?

Ein View kann ungeeignet sein, wenn:

- intensive Schreibzugriffe nötig sind,
- die Zuordnung die Bedeutung der Daten verändert,
- Abfragen sehr teuer werden,
- Verbraucher tabellenspezifisches Verhalten benötigen,
- die Kompatibilitätsschicht keine festgelegte Lebensdauer hat.

## Zusammenfassung

Compatibility View ist eine wirksame Übergangsschicht. Das Datenmodell kann sich weiterentwickeln, ohne gleichzeitig alle Berichte und Integrationen umzustellen.

Das Problem darf aber nicht dauerhaft verborgen werden.

Ein guter Compatibility View besitzt einen klar definierten Vertrag, Ergebnistests, einen akzeptablen Ausführungsplan, einen Verantwortlichen, Nutzungsüberwachung und ein Abschaltdatum.

Er soll Zeit für die Migration gewinnen und nicht die Schemaentwicklung stoppen.
