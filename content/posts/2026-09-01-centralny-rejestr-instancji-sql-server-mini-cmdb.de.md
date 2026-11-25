---
title: "Zentrales SQL-Server-Instanzverzeichnis — eine Mini-CMDB für DBAs"
date: 2026-09-01
slug: zentrales-sql-server-instanzverzeichnis-mini-cmdb
description: "Ein zentrales SQL-Server-Verzeichnis mit Versionen, Umgebungen, Verantwortlichen, Monitoringstatus und Scan-Historie aufbauen."
tags: [SQLServer, CMDB, DBA, Automation, PowerShell, Inventory]
categories: [SQL Server]
draft: false
---

Wer mehrere oder Dutzende SQL-Server-Instanzen verwaltet, stellt sich früher oder später die Frage:

> Weiß ich genau, was ich verwalte?

Eine Serverliste in Excel reicht schnell nicht mehr aus. Ein zentrales Instanzverzeichnis — eine speziell für SQL Server entwickelte Mini-CMDB — kann helfen.

## Welche Informationen sollten gespeichert werden?

- Server- und Instanzname,
- Port,
- Umgebung,
- Version und Build,
- Edition,
- Betriebssystem,
- technischer Verantwortlicher,
- fachlicher Verantwortlicher,
- Monitoringstatus,
- Datum des letzten Scans,
- Verbindungsstatus.

## Beispieltabelle

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

## Scan-Historie

Der aktuelle Zustand allein reicht nicht. Es lohnt sich, die Historie zu speichern:

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

## Von der Instanz erfasste Daten

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

## Ablauf des Collectors

1. Instanzliste einlesen.
2. Verbindung zu jeder Instanz herstellen.
3. Inventarisierungsabfrage ausführen.
4. Ergebnis in der zentralen Datenbank speichern.
5. Verbindungsfehler protokollieren.
6. Bericht über fehlende Informationen erzeugen.

## Was bringt ein zentrales Verzeichnis?

Es bildet die Grundlage für:

- Patch Management,
- Konfigurationsaudits,
- Backupkontrolle,
- Jobmonitoring,
- Kapazitätsanalyse,
- Migrationen,
- Auditberichte.

## Zusammenfassung

Eine Mini-CMDB muss kein riesiges Projekt sein.

Man kann mit einer Tabelle, einem einfachen Collector und einem täglichen Bericht beginnen.

Ein besonnener DBA sucht Server nicht in alten Excel-Dateien.

Er hat einen zentralen Ort, der die Frage beantwortet:

> Welche Instanzen betreiben wir, in welchem Zustand befinden sie sich und wer ist für sie verantwortlich?
