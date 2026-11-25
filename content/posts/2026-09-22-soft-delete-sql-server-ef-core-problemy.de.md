---
title: "Soft Delete in SQL Server und EF Core — bequem, aber nicht ohne Risiken"
date: 2026-09-22
slug: soft-delete-sql-server-ef-core-fallstricke
description: "Soft Delete in SQL Server und EF Core: globale Abfragefilter, gefilterte eindeutige Indizes, Auditierung, Beziehungen und typische Fallstricke."
tags: [SQLServer, EFCore, SoftDelete, Indexes, DataModeling]
categories: [SQL Server]
draft: false
---

Bei Soft Delete wird ein Datensatz als gelöscht markiert, ohne ihn physisch aus der Tabelle zu entfernen.

Meist werden `IsDeleted`, `DeletedAt` und `DeletedBy` ergänzt.

Dieser Ansatz beeinflusst jedoch Eindeutigkeit, Indizes, Beziehungen, Berichte und Aufbewahrung.

## Beispielmodell

```sql
CREATE TABLE dbo.Customer
(
    CustomerId int IDENTITY(1,1) NOT NULL,
    Email nvarchar(320) NOT NULL,
    DisplayName nvarchar(200) NOT NULL,
    IsDeleted bit NOT NULL
        CONSTRAINT DF_Customer_IsDeleted DEFAULT (0),
    DeletedAt datetime2(0) NULL,
    DeletedBy nvarchar(200) NULL,
    CONSTRAINT PK_Customer PRIMARY KEY CLUSTERED (CustomerId)
);
```

## Das Problem mit der Eindeutigkeit

Eine normale `UNIQUE`-Constraint verhindert, dass eine E-Mail-Adresse nach einem Soft Delete erneut verwendet werden kann.

Ein gefilterter Index löst dieses Problem:

```sql
CREATE UNIQUE INDEX UX_Customer_Email_Active
ON dbo.Customer(Email)
WHERE IsDeleted = 0;
```

## Global Query Filter in EF Core

```csharp
public sealed class CustomerConfiguration
    : IEntityTypeConfiguration<Customer>
{
    public void Configure(EntityTypeBuilder<Customer> builder)
    {
        builder.HasQueryFilter(customer => !customer.IsDeleted);
    }
}
```

Um den Filter zu umgehen:

```csharp
var allCustomers = await dbContext.Customers
    .IgnoreQueryFilters()
    .ToListAsync();
```

## Beziehungen und Kaskaden

Was soll mit Bestellungen passieren, wenn der zugehörige Kunde per Soft Delete gelöscht wird?

Mögliche Varianten:

- Bestellungen bleiben sichtbar,
- Bestellungen werden unsichtbar,
- Bestellungen erhalten ebenfalls Soft Delete,
- das Löschen des Kunden ist verboten.

Die Regel muss ausdrücklich entworfen werden.

## Auditierung

Soft Delete ist kein vollständiges Audit. Frühere Werte oder Gründe für Änderungen werden nicht dokumentiert.

Für eine vollständige Historie können erforderlich sein:

- temporale Tabellen,
- eine Audittabelle,
- CDC,
- Anwendungslogs.

## Zusammenfassung

Soft Delete ist ein fachliches Muster und nicht bloß eine zusätzliche Spalte.

Ein sorgfältiger Datenmodellierer fragt:

> Warum müssen die Daten erhalten bleiben, wer darf sie sehen und was bedeutet ihre Wiederherstellung?
