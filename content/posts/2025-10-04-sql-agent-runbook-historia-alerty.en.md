---
title: "SQL Agent Runbook for Alerts and Job History — Retain, Purge, Monitor"
date: "2025-10-04"
slug: "sql-agent-runbook-historia-alerty"
draft: false
description: "A practical runbook for extending job history, automating cleanup, and configuring alerts and operators without using the GUI."
tags: ["SQL Server", "SQL Agent", "Runbook", "Monitoring", "DBA"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/sql-agent-runbook-historia-alerty.png"
canonical: "https://sqlmaniak.blog/sql-agent-runbook-historia-alerty"
---

## Introduction

Is your job history disappearing? Are alerts not reaching anyone? The following scripts are intended as a starting point for configuring SQL Server Agent once and monitoring it consistently.

## Extend Job History

```sql
EXEC msdb.dbo.sp_set_sqlagent_properties
  @jobhistory_max_rows = 200000,
  @jobhistory_max_rows_per_job = 5000;
```

## Regular Cleanup

```sql
-- Raz dziennie wyczyść „szum” starszy niż 30 dni
EXEC msdb.dbo.sp_purge_jobhistory @oldest_date = DATEADD(day,-30,GETDATE());
```

## Operator and Critical Alert (Severity 20–25)

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

**Important:** The sample alert definition uses an event-description keyword and severity 0; it should not be assumed to reliably capture every severity 20–25 error. Verify the supported alert configuration, severity matching, Database Mail, operator notifications, and the SQL Server Agent log before production deployment.

## Monitor SQL Server Agent Health

- Is the `SQLSERVERAGENT` service running?
- Is any job stuck or running unusually long?
- Raise an alert when no successful job runs have been recorded for a defined number of hours.

> Add a Grafana dashboard showing successful and failed job runs per hour and the longest job durations.

Test the notification path end to end, rather than relying only on the fact that the operator or alert object exists.
