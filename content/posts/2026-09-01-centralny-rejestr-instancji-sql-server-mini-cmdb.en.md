---
title: "Central SQL Server Instance Registry — A Mini-CMDB for DBAs"
date: 2026-09-01
slug: central-sql-server-instance-registry-mini-cmdb
description: "Build a central SQL Server inventory that tracks versions, environments, owners, monitoring status, and scan history."
tags: [SQLServer, CMDB, DBA, Automation, PowerShell, Inventory]
categories: [SQL Server]
draft: false
---

An administrator responsible for several or dozens of SQL Server instances eventually asks:

> Do I know exactly what I manage?

A list of servers in Excel quickly becomes insufficient. A central instance registry — a mini-CMDB built for SQL Server — can provide the answer.

## What Information Should You Store?

- server and instance name,
- port,
- environment,
- version and build,
- edition,
- operating system,
- technical owner,
- business owner,
- monitoring status,
- last scan date,
- connection status.

## Example Table

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

## Scan History

The current state alone is not enough. Keep historical records:

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

## Data Collected from an Instance

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

## Collector Workflow

1. Read the instance list.
2. Connect to each instance.
3. Run the inventory query.
4. Save the result in the central database.
5. Record connection errors.
6. Generate a report of missing information.

## What Does a Central Registry Provide?

It becomes the foundation for:

- patch management,
- configuration auditing,
- backup verification,
- job monitoring,
- capacity analysis,
- migrations,
- audit reporting.

## Summary

A mini-CMDB does not have to be a huge project.

Start with one table, a simple collector, and a daily report.

A calm DBA does not search old Excel files for servers.

They have one place that answers:

> Which instances do we maintain, what is their condition, and who is responsible for them?
