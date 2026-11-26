---
title: "Foreign Keys ohne Überraschungen: Beziehungen auf bestehenden Daten sicher einführen"
date: 2026-11-25T08:00:00+01:00
slug: "foreign-key-bezpieczne-wdrozenie"
description: "Einen Fremdschlüssel im bestehenden Datenmodell hinzufügen: zuerst verwaiste Datensätze finden, dann referenzielle Integrität erzwingen."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - foreign key
  - schema evolution
  - data quality
  - database DevOps
draft: false
---

# Foreign Keys ohne Überraschungen: Beziehungen auf bestehenden Daten sicher einführen

Einen Fremdschlüssel zu einer leeren Tabelle hinzuzufügen ist einfach.

In einem bestehenden System muss zuerst geprüft werden, ob die Daten die neue Regel bereits erfüllen.

## Verwaiste Datensätze finden

```sql
SELECT c.CustomerId
FROM dbo.Orders AS c
LEFT JOIN dbo.Customers AS p
    ON p.CustomerId = c.CustomerId
WHERE p.CustomerId IS NULL;
```

Wenn die Abfrage Zeilen liefert, repariert der Constraint diese Daten nicht automatisch.

## Zuerst die Daten bereinigen

Kläre die Bedeutung der verwaisten Datensätze:

- Historische Datenfehler.
- Gelöschte übergeordnete Datensätze.
- Fehlender Backfill.
- Zulässige geschäftliche Ausnahme.

## Constraint hinzufügen

```sql
ALTER TABLE dbo.Orders WITH CHECK
ADD CONSTRAINT FK_Orders_Customers
FOREIGN KEY (CustomerId)
REFERENCES dbo.Customers(CustomerId);
```

`WITH CHECK` validiert die vorhandenen Daten.

## Nicht vertrauenswürdige Constraints

Ein mit `WITH NOCHECK` erstellter Constraint kann existieren, ohne dass die Engine ihm vertraut.

Prüfe:

```sql
SELECT
    name,
    is_disabled,
    is_not_trusted
FROM sys.foreign_keys
WHERE parent_object_id = OBJECT_ID(N'dbo.Orders');
```

## Spätere Validierung

Wenn die Migration eine Übergangsphase benötigt, bereinige zunächst die Daten und führe danach aus:

```sql
ALTER TABLE dbo.Orders WITH CHECK
CHECK CONSTRAINT FK_Orders_Customers;
```

## Performance

Für die Spalte auf der Child-Seite ist meist ein geeigneter Index sinnvoll, besonders bei häufigen Joins und beim Löschen übergeordneter Datensätze.

## Zusammenfassung

Ein Foreign Key ist nicht nur eine Modelldeklaration. Er belegt, dass die bestehenden Daten die Beziehung erfüllen.

Zuerst Datenqualität, dann Erzwingung.
