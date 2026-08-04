---
title: "Centralny rejestr instancji SQL Server — własny mini-CMDB dla DBA"
date: 2026-09-01
slug: centralny-rejestr-instancji-sql-server-mini-cmdb
description: "Jak zbudować centralny rejestr instancji SQL Server przechowujący wersje, środowiska, właścicieli, status monitoringu i historię skanowania."
tags: [SQLServer, CMDB, DBA, Automation, PowerShell, Inventory]
categories: [SQL Server]
draft: false
---

Administrator odpowiedzialny za kilka lub kilkadziesiąt instancji SQL Server prędzej czy później zadaje sobie pytanie:

> Czy wiem dokładnie, czym zarządzam?

Lista serwerów w Excelu szybko przestaje wystarczać. Rozwiązaniem może być centralny rejestr instancji — mini-CMDB przygotowany dla SQL Server.

## Jakie informacje przechowywać?

- nazwę serwera i instancji,
- port,
- środowisko,
- wersję i build,
- edycję,
- system operacyjny,
- właściciela technicznego,
- właściciela biznesowego,
- status monitoringu,
- datę ostatniego skanowania,
- status połączenia.

## Przykładowa tabela

```sql
CREATE SCHEMA inventory;
GO

CREATE TABLE inventory.SqlInstance
(
    SqlInstanceId int IDENTITY(1,1) NOT NULL,
    ServerName sysname NOT NULL,
    InstanceName sysname NULL,
    Port int NULL,
    EnvironmentCode varchar(20) NOT NULL,
    ProductVersion varchar(50) NULL,
    ProductLevel varchar(50) NULL,
    Edition nvarchar(200) NULL,
    TechnicalOwner nvarchar(200) NULL,
    BusinessOwner nvarchar(200) NULL,
    MonitoringEnabled bit NOT NULL
        CONSTRAINT DF_SqlInstance_MonitoringEnabled DEFAULT (1),
    LastScanAt datetime2(0) NULL,
    LastConnectionStatus varchar(30) NULL,
    IsActive bit NOT NULL
        CONSTRAINT DF_SqlInstance_IsActive DEFAULT (1),
    CreatedAt datetime2(0) NOT NULL
        CONSTRAINT DF_SqlInstance_CreatedAt DEFAULT (SYSDATETIME()),
    CONSTRAINT PK_SqlInstance PRIMARY KEY CLUSTERED (SqlInstanceId),
    CONSTRAINT UQ_SqlInstance_Server_Instance
        UNIQUE (ServerName, InstanceName)
);
GO
```

## Historia skanowania

Aktualny stan to za mało. Warto przechowywać historię:

```sql
CREATE TABLE inventory.InstanceScan
(
    InstanceScanId bigint IDENTITY(1,1) NOT NULL,
    SqlInstanceId int NOT NULL,
    ScanStartedAt datetime2(0) NOT NULL,
    ScanFinishedAt datetime2(0) NULL,
    ScanStatus varchar(30) NOT NULL,
    ErrorMessage nvarchar(4000) NULL,
    ProductVersion varchar(50) NULL,
    Edition nvarchar(200) NULL,
    DatabaseCount int NULL,
    CONSTRAINT PK_InstanceScan PRIMARY KEY CLUSTERED (InstanceScanId)
);
GO
```

## Dane zbierane z instancji

```sql
SELECT
    SERVERPROPERTY('MachineName') AS MachineName,
    SERVERPROPERTY('ServerName') AS ServerName,
    SERVERPROPERTY('InstanceName') AS InstanceName,
    SERVERPROPERTY('ProductVersion') AS ProductVersion,
    SERVERPROPERTY('ProductLevel') AS ProductLevel,
    SERVERPROPERTY('Edition') AS Edition,
    host_platform,
    host_distribution,
    host_release
FROM sys.dm_os_host_info;
```

## Schemat działania kolektora

1. Odczytaj listę instancji.
2. Połącz się z każdą instancją.
3. Wykonaj zapytanie inwentaryzacyjne.
4. Zapisz wynik w bazie centralnej.
5. Zapisz błąd połączenia.
6. Wygeneruj raport braków.

## Co daje centralny rejestr?

Staje się fundamentem dla:

- patch management,
- audytu konfiguracji,
- kontroli backupów,
- monitoringu jobów,
- analizy pojemności,
- migracji,
- raportowania dla audytu.

## Podsumowanie

Mini-CMDB nie musi być ogromnym projektem.

Można rozpocząć od jednej tabeli, prostego kolektora i codziennego raportu.

Spokojny DBA nie szuka serwerów w starych plikach Excel.

Ma jedno miejsce, które odpowiada na pytanie:

> Jakie instancje utrzymujemy, w jakim są stanie i kto za nie odpowiada?
