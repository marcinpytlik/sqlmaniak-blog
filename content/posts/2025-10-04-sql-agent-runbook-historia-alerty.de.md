---
title: "SQL-Agent-Runbook für Alerts und Jobhistorie — Aufbewahren, Bereinigen, Überwachen"
date: "2025-10-04"
slug: "sql-agent-runbook-historia-alerty"
draft: false
description: "Praxis-Runbook zur Verlängerung der Jobhistorie, automatischen Bereinigung und Einrichtung von Alerts und Operatoren ohne GUI."
tags: ["SQL Server", "SQL Agent", "Runbook", "Monitoring", "DBA"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/sql-agent-runbook-historia-alerty.png"
---

## Einleitung

Verschwindet deine Jobhistorie? Kommen Alerts nicht an? Die folgenden Skripte sind ein Ausgangspunkt, um SQL Server Agent einmal sinnvoll einzurichten und anschließend zuverlässig zu überwachen.

## Jobhistorie verlängern

```sql
EXEC msdb.dbo.sp_set_sqlagent_properties
  @jobhistory_max_rows = 200000,
  @jobhistory_max_rows_per_job = 5000;
```

## Regelmäßige Bereinigung

```sql
-- Raz dziennie wyczyść „szum” starszy niż 30 dni
EXEC msdb.dbo.sp_purge_jobhistory @oldest_date = DATEADD(day,-30,GETDATE());
```

## Operator und kritischer Alert (Severity 20–25)

```sql
EXEC msdb.dbo.sp_add_operator @name = N'DBA-OnCall', @email_address = N'dba@contoso.local';

EXEC msdb.dbo.sp_add_alert
  @name=N'Błędy krytyczne (20-25)',
  @message_id=0, @severity=0, @include_event_description_in=1,
  @notification_message=N'Krytyczny błąd na serwerze', @delay_between_responses=600,
  @job_id=NULL, @database_name=N'',
  @event_description_keyword=N'Error: 2[0-5]',
  @performance_condition=NULL, @wmi_namespace=NULL, @wmi_query=NULL,
  @has_notification=1;
EXEC msdb.dbo.sp_add_notification @alert_name=N'Błędy krytyczne (20-25)', @operator_name=N'DBA-OnCall', @notification_method=1;
```

**Wichtig:** Die Beispieldefinition verwendet ein Schlüsselwort in der Ereignisbeschreibung und Severity 0. Sie sollte nicht als zuverlässige Erkennung aller Fehler mit Severity 20–25 betrachtet werden. Prüfe die unterstützte Alert-Konfiguration, die Severity-Filterung, Database Mail, Operatorbenachrichtigungen und das SQL-Server-Agent-Protokoll vor dem Produktionseinsatz.

## SQL Server Agent überwachen

- Läuft der Dienst `SQLSERVERAGENT`?
- Hängt ein Job oder läuft er ungewöhnlich lange?
- Erzeuge einen Alert, wenn über eine definierte Anzahl von Stunden kein erfolgreicher Joblauf protokolliert wurde.

> Ergänze ein Grafana-Dashboard mit erfolgreichen und fehlgeschlagenen Jobläufen pro Stunde sowie den längsten Laufzeiten.

Teste den vollständigen Benachrichtigungsweg, statt dich allein auf die Existenz eines Operators oder Alert-Objekts zu verlassen.
