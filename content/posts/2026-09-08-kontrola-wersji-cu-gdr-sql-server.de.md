---
title: "SQL-Server-Versionen, CUs und GDRs auf mehreren Instanzen kontrollieren"
date: 2026-09-08
slug: sql-server-versionen-cu-gdr-mehrere-instanzen-kontrollieren
description: "Praxisansatz zur Inventarisierung von SQL-Server-Builds, Unterscheidung von CU und GDR und Planung des Patchings vieler Instanzen."
tags: [SQLServer, CU, GDR, Patching, DBA, Security]
categories: [SQL Server]
draft: false
---

Eine einzelne SQL-Server-Instanz zu patchen ist eine technische Aufgabe.

Das Patching von Dutzenden Instanzen wird zu einem Managementprozess.

## Instanzversion auslesen

```sql
SELECT
    @@SERVERNAME AS ServerName,
    SERVERPROPERTY('ProductVersion') AS ProductVersion,
    SERVERPROPERTY('ProductLevel') AS ProductLevel,
    SERVERPROPERTY('Edition') AS Edition,
    SERVERPROPERTY('ProductUpdateLevel') AS ProductUpdateLevel,
    SERVERPROPERTY('ProductUpdateReference') AS ProductUpdateReference;
```

Entscheidend ist die vollständige Buildnummer. „SQL Server 2022“ allein reicht nicht aus.

## CU und GDR

Ein CU enthält einen kumulativen Satz von Fehlerbehebungen. GDR-Updates betreffen vor allem Sicherheitskorrekturen und kritische Fixes für einen bestimmten Wartungszweig.

Die wichtigste Regel:

> Vergleiche die vollständige Buildnummer mit der freigegebenen Baseline deiner Organisation.

## Baseline-Tabelle

```sql
CREATE SCHEMA patch;
GO

CREATE TABLE patch.SqlBuildBaseline
(
    SqlBuildBaselineId int IDENTITY(1,1) NOT NULL,
    MajorVersion int NOT NULL,
    ProductVersion varchar(50) NOT NULL,
    UpdateType varchar(20) NOT NULL,
    UpdateName varchar(100) NULL,
    ReleaseDate date NULL,
    IsApproved bit NOT NULL,
    IsCurrentTarget bit NOT NULL,
    Notes nvarchar(1000) NULL,
    CONSTRAINT PK_SqlBuildBaseline
        PRIMARY KEY CLUSTERED (SqlBuildBaselineId),
    CONSTRAINT UQ_SqlBuildBaseline_ProductVersion
        UNIQUE (ProductVersion)
);
GO
```

## Patching-Historie

Erfasse:

- Build vor dem Update,
- Build nach dem Update,
- Start- und Endzeit,
- Status,
- Änderungsnummer,
- Validierungsergebnis,
- Information über den Neustart.

## Validierung nach dem Patching

Prüfe:

- Engine-Version,
- Dienstestatus,
- SQL Server Error Log,
- Datenbankstatus,
- Always On oder FCI,
- SQL Server Agent,
- kritische Jobs,
- Database Mail,
- Backups,
- Monitoring.

```sql
SELECT
    name,
    state_desc,
    user_access_desc,
    recovery_model_desc
FROM sys.databases
ORDER BY name;
```

## Gesamter Prozess

1. Inventarisierung.
2. Ziel-Build auswählen.
3. Anforderungen analysieren.
4. Labortest durchführen.
5. Rollback-Plan vorbereiten.
6. Wartungsfenster festlegen.
7. Update installieren.
8. Neustart.
9. Validierung.
10. Dokumentation aktualisieren.

## Zusammenfassung

Die Kontrolle von CUs und GDRs erfordert ein zentrales Inventar, eine Baseline, Historie und Validierung.

Ein besonnener DBA patcht nicht aus dem Gedächtnis.

Er patcht seine Instanzen auf Grundlage von Daten, Standards und einem dokumentierten Prozess.
