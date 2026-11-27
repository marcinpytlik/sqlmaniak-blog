---
title: "Parallel Table: Migration in eine neue Tabelle ohne riskanten Umbau der alten"
date: 2026-09-09T00:01:00+02:00
slug: "parallel-table-migration"
description: "Eine neue Tabelle neben der alten aufbauen, Daten migrieren und die Anwendung kontrolliert umstellen."
category: "Relationale Renaissance"
tags: [SQL Server, Parallel Table, Tabellenmigration, Schema Evolution, Zero Downtime]
draft: false
---

# Parallel Table: Migration in eine neue Tabelle ohne riskanten Umbau der alten

Manchmal ist eine Modelländerung zu umfangreich für einige `ALTER TABLE`-Anweisungen. Wir ändern beispielsweise:

- den Primärschlüssel,
- die Partitionierung,
- die Komprimierung,
- Datentypen,
- die Indexstruktur,
- die Speicherung der Historie,
- die Bedeutung bestimmter Spalten.

Dann lässt sich **eine neue Tabelle parallel zur alten** aufbauen.

Das Muster Parallel Table sieht so aus:

1. V2-Tabelle erstellen.
2. Historische Daten kopieren.
3. Laufende Änderungen synchronisieren.
4. Beide Modelle vergleichen.
5. Lese- und Schreibzugriffe umstellen.
6. Alte Tabelle für eine Sicherheitsfrist behalten.
7. Nach bestätigter Korrektheit entfernen.

> Statt das Fundament unter einem bewohnten Gebäude umzubauen, errichten wir daneben ein neues und leiten den Verkehr um.

## Beispiel

Die alte Tabelle:

```sql
CREATE TABLE dbo.Orders
(
    OrderId    int IDENTITY(1,1) NOT NULL,
    CustomerId int NOT NULL,
    Amount     money NOT NULL,
    CreatedAt  datetime NOT NULL,

    CONSTRAINT PK_Orders
        PRIMARY KEY (OrderId)
);
```

Das neue Modell verwendet:

- `bigint` als Identifikator,
- `decimal` statt `money`,
- `datetime2`,
- einen expliziten Status,
- eine andere Indexstruktur.

```sql
CREATE TABLE dbo.OrdersV2
(
    OrderId     bigint NOT NULL,
    CustomerId  int NOT NULL,
    Amount      decimal(19,4) NOT NULL,
    OrderStatus varchar(20) NOT NULL,
    CreatedAt   datetime2(0) NOT NULL,

    CONSTRAINT PK_OrdersV2
        PRIMARY KEY CLUSTERED (OrderId),

    CONSTRAINT CK_OrdersV2_Status
        CHECK (OrderStatus IN ('New', 'Paid', 'Cancelled'))
);
```

## Historische Daten kopieren

```sql
INSERT INTO dbo.OrdersV2
(
    OrderId,
    CustomerId,
    Amount,
    OrderStatus,
    CreatedAt
)
SELECT
    CONVERT(bigint, OrderId),
    CustomerId,
    CONVERT(decimal(19,4), Amount),
    'Paid',
    CONVERT(datetime2(0), CreatedAt)
FROM dbo.Orders;
```

Bei einer großen Tabelle sollte die Migration in Batches erfolgen und der Fortschritt gespeichert werden.

## Änderungen synchronisieren

Die schwierigste Frage lautet: Was passiert mit Datensätzen, die während des Kopierens geändert werden?

Mögliche Strategien:

### Kurzes schreibgeschütztes Zeitfenster

Die einfachste Lösung: Schreibzugriffe stoppen, letzte Änderungen kopieren und die Tabelle umstellen. Geeignet, wenn ein kurzes Wartungsfenster akzeptabel ist.

### Dual Write

Die Anwendung schreibt in beide Tabellen. Das erfordert Atomarität und Konsistenzüberwachung.

### Change Data Capture

Zunächst wird der Grundbestand kopiert, danach werden Änderungen aus CDC nachgespielt.

### Synchronisationstrigger

Ein Trigger schreibt Änderungen in V2. Das ist konzeptionell einfach, erhöht aber die Kosten jeder Operation und verbirgt Logik.

### Änderungswarteschlange

Operationen landen in einer Queue-Tabelle, und ein separater Prozess übernimmt sie in das neue Modell.

Die Auswahl hängt von Ausfallzeitanforderungen, Skalierung und der Toleranz gegenüber vorübergehender Inkonsistenz ab.

## Validierung

Ein Vergleich der Zeilenzahlen ist notwendig, aber nicht ausreichend.

```sql
SELECT
    OldCount = (SELECT COUNT_BIG(*) FROM dbo.Orders),
    NewCount = (SELECT COUNT_BIG(*) FROM dbo.OrdersV2);
```

Vergleiche außerdem:

```sql
SELECT
    OldAmount = SUM(CONVERT(decimal(38,4), Amount))
FROM dbo.Orders;

SELECT
    NewAmount = SUM(CONVERT(decimal(38,4), Amount))
FROM dbo.OrdersV2;
```

Weitere Prüfungen:

- fehlende Schlüssel,
- Duplikate,
- konvertierte Werte,
- Statusverteilung,
- Datumsbereiche,
- zufällige Datensatzstichproben,
- Ergebnisse wichtiger Geschäftsabfragen.

## Cutover

Die Umstellung kann erfolgen über:

- Anwendungskonfiguration,
- Stored Procedures,
- ein Synonym,
- einen View,
- Umbenennung der Tabellen.

Beispiel mit Synonym:

```sql
CREATE SYNONYM app.Orders
FOR dbo.OrdersV2;
```

Ein Synonym erleichtert den Wechsel des Zielobjekts, unterstützt aber nicht alle Szenarien und verlangt Vorsicht bei Schemaabhängigkeiten. Das Schema `app` muss zuvor existieren.

Das Umbenennen von Tabellen wirkt elegant, ist aber riskant. Es aktualisiert nicht alle Referenzen und kann zwischen einzelnen Operationen vorübergehend Fehler auslösen.

## Identität und neue Datensätze

Erzeugen beide Tabellen Identifikatoren, können Kollisionen entstehen. Besser ist es:

- Schlüssel zentral zu generieren,
- den Identifikator an beide Tabellen zu übergeben,
- eine Sequence zu verwenden,
- Wertebereiche zu reservieren,
- den Generator vor Schreibzugriffen auf V2 umzustellen.

Beispielsequenz:

```sql
CREATE SEQUENCE dbo.OrderIdSequence
    AS bigint
    START WITH 1000000
    INCREMENT BY 1;
```

## Rückkehr zur alten Tabelle

V1 sollte nach dem Cutover nicht sofort gelöscht werden. Sie kann als Vergleichsbasis und Notfalloption dienen.

Allerdings muss geklärt sein:

- ob V1 weiterhin Schreibzugriffe erhält,
- wie lange sie aufbewahrt wird,
- ob ein Rollback nach V2-spezifischen Daten noch möglich ist,
- wann die Tabelle zum schreibgeschützten Archiv wird.

## Wann einsetzen?

Parallel Table eignet sich, wenn:

- die Strukturänderung umfangreich ist,
- neue Indizes oder Partitionierung erforderlich sind,
- eine In-Place-Konvertierung riskant wäre,
- V1 und V2 verglichen werden sollen,
- ausreichend Speicherplatz für parallele Daten vorhanden ist.

## Kosten

Die größten Kosten sind Speicherplatz und Synchronisation. Eine Zeit lang werden zwei vollständige Datenbestände vorgehalten. Zusätzlich müssen berücksichtigt werden:

- laufende Änderungen,
- Schlüssel,
- Constraints,
- Stored Procedures,
- Berechtigungen,
- Statistiken und Indizes,
- Backup und Hochverfügbarkeit.

## Zusammenfassung

Parallel Table ist ein starkes Muster, weil es eine klare Grenze zwischen altem und neuem Modell schafft. V2 kann aufgebaut, mit echten Daten getestet und erst bei Bereitschaft produktiv geschaltet werden.

Es geht aber um mehr als `INSERT ... SELECT`. Entscheidend sind Delta-Synchronisation, fachliche Validierung, kontrollierter Cutover, Rollback- oder Roll-forward-Plan und das Ende der Parallelphase.

Eine neue Tabelle neben der alten kann sicherer sein als ein Umbau am bestehenden Objekt — sofern wir genau planen, wann beide Versionen aufhören, parallel zu existieren.
