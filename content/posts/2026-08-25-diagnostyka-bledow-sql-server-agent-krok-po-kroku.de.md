---
title: "Warum ist ein SQL-Server-Agent-Job fehlgeschlagen? Diagnose Schritt für Schritt"
date: 2026-08-25
slug: sql-server-agent-jobfehler-schrittweise-diagnostizieren
description: "Systematische Diagnose von SQL-Server-Agent-Jobfehlern: Historie, erster fehlerhafter Schritt, Ausführungskonto, Proxy, Zeitplan und Logs."
tags: [SQLServer, SQLServerAgent, Troubleshooting, Jobs, DBA]
categories: [SQL Server]
draft: false
---

„The job failed“ ist keine Diagnose.

Eine echte Fehlersuche beginnt mit der Frage, welcher Schritt zuerst fehlgeschlagen ist, in welchem Sicherheitskontext er ausgeführt wurde und was sich seit der letzten erfolgreichen Ausführung geändert hat.

## Schritt 1. Den ersten fehlgeschlagenen Schritt finden

```sql
SELECT TOP (100)
    j.name AS JobName,
    msdb.dbo.agent_datetime(h.run_date, h.run_time) AS RunDateTime,
    h.step_id,
    h.step_name,
    h.run_status,
    h.sql_severity,
    h.sql_message_id,
    h.message
FROM msdb.dbo.sysjobhistory AS h
INNER JOIN msdb.dbo.sysjobs AS j
    ON h.job_id = j.job_id
WHERE j.name = N'TwojJob'
ORDER BY h.instance_id DESC;
```

## Schritt 2. Die Schrittkonfiguration prüfen

```sql
SELECT
    j.name AS JobName,
    s.step_id,
    s.step_name,
    s.subsystem,
    s.database_name,
    s.command,
    s.retry_attempts,
    s.retry_interval,
    s.on_success_action,
    s.on_fail_action,
    s.proxy_id,
    s.output_file_name
FROM msdb.dbo.sysjobsteps AS s
INNER JOIN msdb.dbo.sysjobs AS j
    ON s.job_id = j.job_id
WHERE j.name = N'TwojJob'
ORDER BY s.step_id;
```

## Schritt 3. Den Sicherheitskontext ermitteln

```sql
SELECT
    j.name AS JobName,
    SUSER_SNAME(j.owner_sid) AS JobOwner,
    s.step_id,
    s.step_name,
    s.subsystem,
    p.name AS ProxyName,
    c.name AS CredentialName,
    c.credential_identity
FROM msdb.dbo.sysjobs AS j
INNER JOIN msdb.dbo.sysjobsteps AS s
    ON j.job_id = s.job_id
LEFT JOIN msdb.dbo.sysproxies AS p
    ON s.proxy_id = p.proxy_id
LEFT JOIN sys.credentials AS c
    ON p.credential_id = c.credential_id
WHERE j.name = N'TwojJob';
```

Ein häufiges Szenario lautet:

> Das Skript funktioniert manuell, aber nicht als Job.

Meist liegt der Unterschied beim Ausführungskonto, PowerShell-Profil, bei Pfaden, Umgebungsvariablen oder dem Zugriff auf eine Netzwerkfreigabe.

## Schritt 4. Jobbesitzer und Zeitplan prüfen

```sql
SELECT
    name AS JobName,
    SUSER_SNAME(owner_sid) AS JobOwner
FROM msdb.dbo.sysjobs
WHERE name = N'TwojJob';
```

Ein Job sollte nicht einem beliebigen Mitarbeiterkonto gehören.

## Schritt 5. Logs des jeweiligen Subsystems prüfen

Bei T-SQL untersuche die Jobhistorie, das SQL Server Error Log und Extended Events.

Bei PowerShell protokolliere die vollständige Ausnahme, den Exitcode und die Logdatei.

Bei SSIS verwende die SSISDB-Berichte.

Bei CmdExec prüfe stdout, stderr, Exitcode und Ausführungskonto.

## Schritt 6. Mit der letzten erfolgreichen Ausführung vergleichen

Prüfe:

- Deployments,
- Passwortänderungen,
- Patching,
- Failover,
- DNS-Änderungen,
- Pfadänderungen,
- fehlenden Speicherplatz,
- Berechtigungsänderungen,
- Parameteränderungen.

## Zusammenfassung

Jobfehler sollten schichtweise untersucht werden: Ausführung, Schritt, Subsystem, Sicherheit, Zeitplan und Abhängigkeiten.

Ein besonnener DBA bleibt nicht bei „job failed“ stehen.

Er findet die erste technische Ursache und nutzt den Vorfall, um den Prozess zu verbessern.
