---
title: "Data Normalization Without Academic Theory — A Practical SQL Server Example"
date: 2026-09-15
slug: data-normalization-practical-sql-server-example
description: "A practical SQL Server data normalization example: from a problematic single table to a consistent relational model."
tags: [SQLServer, DataModeling, Normalization, DatabaseDesign, DBA]
categories: [SQL Server]
draft: false
---

Normalization is often associated with theory. In practice, its purpose is simple:

> Store data without duplicating facts or creating contradictions.

## Initial Model

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

Problems arise when a customer places multiple orders or a single order has multiple line items.

## What Problems Does This Create?

### Update anomaly

Changing a customer's email address requires updating multiple rows.

### Insertion anomaly

You cannot add a product until it appears in an order.

### Deletion anomaly

Deleting the last order might remove the only information about a customer.

## Separate the Customer

```sql
CREATE TABLE dbo.Customer
(
    CustomerId int IDENTITY(1,1) NOT NULL,
    CustomerName nvarchar(200) NOT NULL,
    Email nvarchar(320) NULL,
    CONSTRAINT PK_Customer PRIMARY KEY CLUSTERED (CustomerId)
);
```

## Separate the Product

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

## Order Header

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

## Order Lines

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

## What Have We Gained?

Each fact has one place:

- the customer in `Customer`,
- the product in `Product`,
- the order in `SalesOrder`,
- the line item in `SalesOrderLine`.

## Summary

Normalization is not an academic ritual. It eliminates repetition and inconsistency.

A careful designer starts with the question:

> Where is the single authoritative place for recording this fact?
