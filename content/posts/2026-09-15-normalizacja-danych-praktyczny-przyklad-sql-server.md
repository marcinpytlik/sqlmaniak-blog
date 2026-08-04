---
title: "Normalizacja danych bez akademickiej teorii — praktyczny przykład w SQL Server"
date: 2026-09-15
slug: normalizacja-danych-praktyczny-przyklad-sql-server
description: "Praktyczny przykład normalizacji modelu danych w SQL Server: od jednej problematycznej tabeli do spójnego modelu relacyjnego."
tags: [SQLServer, DataModeling, Normalization, DatabaseDesign, DBA]
categories: [SQL Server]
draft: false
---

Normalizacja często kojarzy się z teorią. W praktyce jej cel jest prosty:

> Zapisać dane tak, aby nie powielać faktów i nie tworzyć sprzeczności.

## Model początkowy

```sql
CREATE TABLE dbo.OrderImport
(
    OrderNumber varchar(30) NOT NULL,
    OrderDate date NOT NULL,
    CustomerName nvarchar(200) NOT NULL,
    CustomerEmail nvarchar(320) NULL,
    ProductCode varchar(30) NOT NULL,
    ProductName nvarchar(200) NOT NULL,
    UnitPrice decimal(18,2) NOT NULL,
    Quantity int NOT NULL
);
```

Problem pojawia się, gdy klient składa wiele zamówień lub jedno zamówienie ma wiele pozycji.

## Jakie problemy powstają?

### Anomalia aktualizacji

Zmiana e-maila klienta wymaga poprawienia wielu wierszy.

### Anomalia dodawania

Nie można dodać produktu, dopóki nie pojawi się w zamówieniu.

### Anomalia usuwania

Usunięcie ostatniego zamówienia może usunąć jedyną informację o kliencie.

## Oddziel klienta

```sql
CREATE TABLE dbo.Customer
(
    CustomerId int IDENTITY(1,1) NOT NULL,
    CustomerName nvarchar(200) NOT NULL,
    Email nvarchar(320) NULL,
    CONSTRAINT PK_Customer PRIMARY KEY CLUSTERED (CustomerId)
);
```

## Oddziel produkt

```sql
CREATE TABLE dbo.Product
(
    ProductId int IDENTITY(1,1) NOT NULL,
    ProductCode varchar(30) NOT NULL,
    ProductName nvarchar(200) NOT NULL,
    CurrentUnitPrice decimal(18,2) NOT NULL,
    CONSTRAINT PK_Product PRIMARY KEY CLUSTERED (ProductId),
    CONSTRAINT UQ_Product_ProductCode UNIQUE (ProductCode)
);
```

## Nagłówek zamówienia

```sql
CREATE TABLE dbo.SalesOrder
(
    SalesOrderId bigint IDENTITY(1,1) NOT NULL,
    OrderNumber varchar(30) NOT NULL,
    OrderDate date NOT NULL,
    CustomerId int NOT NULL,
    CONSTRAINT PK_SalesOrder PRIMARY KEY CLUSTERED (SalesOrderId),
    CONSTRAINT UQ_SalesOrder_OrderNumber UNIQUE (OrderNumber),
    CONSTRAINT FK_SalesOrder_Customer
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customer(CustomerId)
);
```

## Pozycje zamówienia

```sql
CREATE TABLE dbo.SalesOrderLine
(
    SalesOrderLineId bigint IDENTITY(1,1) NOT NULL,
    SalesOrderId bigint NOT NULL,
    ProductId int NOT NULL,
    Quantity int NOT NULL,
    UnitPrice decimal(18,2) NOT NULL,
    CONSTRAINT PK_SalesOrderLine
        PRIMARY KEY CLUSTERED (SalesOrderLineId),
    CONSTRAINT FK_SalesOrderLine_SalesOrder
        FOREIGN KEY (SalesOrderId)
        REFERENCES dbo.SalesOrder(SalesOrderId),
    CONSTRAINT FK_SalesOrderLine_Product
        FOREIGN KEY (ProductId)
        REFERENCES dbo.Product(ProductId),
    CONSTRAINT CK_SalesOrderLine_Quantity CHECK (Quantity > 0)
);
```

## Co zyskaliśmy?

Każdy fakt ma jedno miejsce:

- klient w `Customer`,
- produkt w `Product`,
- zamówienie w `SalesOrder`,
- pozycja w `SalesOrderLine`.

## Podsumowanie

Normalizacja nie jest akademickim rytuałem. Eliminuje powtórzenia i niespójności.

Spokojny projektant zaczyna od pytania:

> Gdzie znajduje się jedyne wiarygodne miejsce zapisu danego faktu?
