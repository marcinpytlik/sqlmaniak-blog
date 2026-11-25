---
title: "Datennormalisierung ohne akademische Theorie — ein praktisches SQL-Server-Beispiel"
date: 2026-09-15
slug: datennormalisierung-praktisches-sql-server-beispiel
description: "Praktisches Beispiel zur Datennormalisierung in SQL Server: von einer problematischen Tabelle zu einem konsistenten relationalen Modell."
tags: [SQLServer, DataModeling, Normalization, DatabaseDesign, DBA]
categories: [SQL Server]
draft: false
---

Normalisierung wird oft mit Theorie verbunden. In der Praxis ist ihr Ziel einfach:

> Daten so speichern, dass Fakten nicht dupliziert werden und keine Widersprüche entstehen.

## Ausgangsmodell

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

Probleme entstehen, wenn ein Kunde mehrere Bestellungen aufgibt oder eine Bestellung mehrere Positionen enthält.

## Welche Probleme entstehen?

### Änderungsanomalie

Eine Änderung der E-Mail-Adresse eines Kunden erfordert die Aktualisierung mehrerer Zeilen.

### Einfügeanomalie

Ein Produkt kann erst angelegt werden, wenn es in einer Bestellung vorkommt.

### Löschanomalie

Das Löschen der letzten Bestellung kann die einzigen Informationen über einen Kunden entfernen.

## Kunden auslagern

```sql
CREATE TABLE dbo.Customer
(
    CustomerId int IDENTITY(1,1) NOT NULL,
    CustomerName nvarchar(200) NOT NULL,
    Email nvarchar(320) NULL,
    CONSTRAINT PK_Customer PRIMARY KEY CLUSTERED (CustomerId)
);
```

## Produkte auslagern

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

## Bestellkopf

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

## Bestellpositionen

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

## Was haben wir gewonnen?

Jede Tatsache hat genau einen Platz:

- der Kunde in `Customer`,
- das Produkt in `Product`,
- die Bestellung in `SalesOrder`,
- die Position in `SalesOrderLine`.

## Zusammenfassung

Normalisierung ist kein akademisches Ritual. Sie verhindert Wiederholungen und Inkonsistenzen.

Ein sorgfältiger Datenmodellierer fragt zuerst:

> Wo befindet sich die einzige maßgebliche Stelle, an der diese Tatsache gespeichert wird?
