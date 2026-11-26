---
title: "Migration von SQL Server 2016 auf 2022 — Was der Upgrade-Assistent verschweigt"
date: 2026-10-06
slug: migracja-sql-server-2016-do-2022-ryzyka
description: "Wichtige Migrationsrisiken: Compatibility Level, Ausführungspläne, Logins, Jobs, SSIS, HA/DR und Tests nach der Migration."
tags: [SQLServer, Migration, SQLServer2022, DBA, Upgrade]
categories: [SQL Server]
draft: false
---

Der Installationsassistent kann viele technische Voraussetzungen prüfen. Er kennt aber weder Geschäftsprozesse und Anwendungsabhängigkeiten noch das Verhalten der wichtigsten Abfragen.

## Zwei Ebenen der Migration

Unterscheide zwischen:

1. Dem Umzug einer Datenbank auf eine neuere Engine.
2. Der Erhöhung des Compatibility Levels.

## Was muss zusätzlich zu den Benutzerdatenbanken migriert werden?

- Logins und SIDs.
- Serverrollen und Berechtigungen.
- Credentials und Proxies.
- Jobs, Operatoren und Alerts.
- Linked Servers und Database Mail.
- Zertifikate und Schlüssel.
- SSISDB.
- Einstellungen der Instanz.

## Verwaiste Benutzer

```sql
SELECT
    dp.name AS DatabaseUser,
    dp.type_desc
FROM sys.database_principals AS dp
LEFT JOIN sys.server_principals AS sp
    ON dp.sid = sp.sid
WHERE dp.authentication_type_desc = 'INSTANCE'
  AND sp.sid IS NULL
  AND dp.name NOT IN
  (
      N'guest',
      N'dbo',
      N'sys',
      N'INFORMATION_SCHEMA'
  );
```

## Compatibility Level

```sql
SELECT
    name,
    compatibility_level
FROM sys.databases
ORDER BY name;
```

Die Änderung:

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

sollte eine eigene Phase mit Query Store und Überwachung von Planregressionen bilden.

## Performance-Risiken

- Parameter Sniffing.
- Kardinalitätsschätzung.
- Scalar UDF Inlining.
- Tabellenvariablen und Multi-Statement Table-Valued Functions (MSTVFs).
- Batch Mode on Rowstore.
- Memory Grants.
- Veraltete Hints.

## Tests nach der Migration

Prüfe Datenbankstatus, `DBCC CHECKDB`, Logins, Jobs, Backups, Monitoring, Anwendungen, Integrationen, Performance, HA/DR, Alerts und das SQL Server Error Log.

## Rollback-Plan

Ein Rollback kann die Rückleitung der Anwendung zur alten Instanz, ein Tail-Log-Backup, die Änderung eines Alias oder DNS-Eintrags, ein Restore und die Rücknahme von Integrationsänderungen umfassen. Plane dies vorher: Nicht jede Migration ist einfach umkehrbar.

## Zusammenfassung

Die Migration endet nicht mit dem Status `ONLINE`. Ein besonnener DBA prüft, ob das gesamte System funktioniert, überwacht wird und sicher wiederhergestellt werden kann.
