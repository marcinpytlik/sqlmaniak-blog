---
title: "SQL Agent: runbook do alertów i historii — wydłuż, czyść, monitoruj"
date: "2025-10-04"
slug: "sql-agent-runbook-historia-alerty"
draft: false
description: "Krótkie i skuteczne: jak wydłużyć historię zadań, sprzątać ją automatycznie, oraz zakładać alerty i operatorów bez klikania."
tags: ["SQL Server", "SQL Agent", "Runbook", "Monitoring", "DBA"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/sql-agent-runbook-historia-alerty.png"
canonical: "https://sqlmaniak.blog/sql-agent-runbook-historia-alerty"
---

Lead
----
Historia zadań znika? Alerty nie dzwonią? Poniżej skrypty, które ustawisz raz — i śpisz spokojniej.

## Wydłuż historię
```sql
EXEC msdb.dbo.sp_set_sqlagent_properties
  @jobhistory_max_rows = 200000,
  @jobhistory_max_rows_per_job = 5000;
```

## Regularne sprzątanie
```sql
-- Raz dziennie wyczyść „szum” starszy niż 30 dni
EXEC msdb.dbo.sp_purge_jobhistory @oldest_date = DATEADD(day,-30,GETDATE());
```

## Operator i alert krytyczny (Severity 20–25)
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

## Monitoruj zdrowie SQL Agent
- `SQLSERVERAGENT` up?  
- Czy nie „wisi” job z długim czasem?  
- Alert, gdy brak „Successful job runs” przez X godzin.

> Dorzuć panel w Grafanie: sukcesy/porażki jobów per godzina, czas trwania najdłuższych.
