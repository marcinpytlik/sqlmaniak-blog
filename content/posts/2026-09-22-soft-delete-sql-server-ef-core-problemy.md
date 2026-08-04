---
title: "Soft Delete w SQL Server i EF Core — wygoda, która może stworzyć problemy"
date: 2026-09-22
slug: soft-delete-sql-server-ef-core-problemy
description: "Soft Delete w SQL Server i EF Core: global query filters, filtrowane indeksy unikalne, audyt, relacje i typowe pułapki."
tags: [SQLServer, EFCore, SoftDelete, Indexes, DataModeling]
categories: [SQL Server]
draft: false
---

Soft Delete polega na oznaczeniu rekordu jako usuniętego bez fizycznego usunięcia go z tabeli.

Najczęściej dodajemy `IsDeleted`, `DeletedAt` i `DeletedBy`.

Rozwiązanie wpływa jednak na unikalność, indeksy, relacje, raporty i retencję.

## Przykładowy model

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

## Problem z unikalnością

Zwykłe ograniczenie `UNIQUE` uniemożliwi ponowne użycie adresu po soft delete.

Rozwiązaniem jest filtrowany indeks:

```sql
CREATE UNIQUE INDEX UX_Customer_Email_Active
ON dbo.Customer(Email)
WHERE IsDeleted = 0;
```

## Global Query Filter w EF Core

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

Aby pominąć filtr:

```csharp
var allCustomers = await dbContext.Customers
    .IgnoreQueryFilters()
    .ToListAsync();
```

## Relacje i kaskady

Co ma się stać z zamówieniami po soft delete klienta?

Możliwe warianty:

- zamówienia pozostają widoczne,
- stają się niewidoczne,
- również otrzymują soft delete,
- usunięcie klienta jest zabronione.

Regułę trzeba zaprojektować jawnie.

## Audyt

Soft Delete nie jest pełnym audytem. Nie pokazuje historii wartości ani przyczyny zmiany.

Do pełnej historii mogą być potrzebne:

- tabele temporalne,
- tabela audytowa,
- CDC,
- log aplikacyjny.

## Podsumowanie

Soft Delete jest wzorcem biznesowym, a nie tylko dodatkową kolumną.

Spokojny projektant pyta:

> Dlaczego dane mają pozostać, kto może je zobaczyć i co oznacza ich przywrócenie?
