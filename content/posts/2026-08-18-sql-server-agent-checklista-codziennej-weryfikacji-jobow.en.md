---
title: "SQL Server Agent Under Control — Daily Job Verification Checklist"
date: 2026-08-18
slug: sql-server-agent-daily-job-verification-checklist
description: "Daily SQL Server Agent job checklist: failures, delays, execution time, disabled jobs, and missing notifications."
tags: [SQLServer, SQLServerAgent, Jobs, DBA, Monitoring, Checklist]
categories: [SQL Server]
draft: false
---

A green icon beside a SQL Server Agent job is not enough to consider the process safe.

A job may report success even though it skipped some steps, started late, or took much longer than usual.

## What Should Daily Checks Detect?

- failed jobs,
- canceled jobs,
- jobs that started late,
- jobs still running,
- unusual execution durations,
- disabled jobs,
- jobs without schedules,
- jobs without notifications.

## Latest Status of All Jobs

```sql
;WITH LastExecution AS
(
    SELECT
        j.job_id,
        j.name AS JobName,
        h.run_status,
        msdb.dbo.agent_datetime(h.run_date, h.run_time) AS RunDateTime,
        h.run_duration,
        h.message,
        ROW_NUMBER() OVER
        (
            PARTITION BY j.job_id
            ORDER BY h.instance_id DESC
        ) AS RowNumber
    FROM msdb.dbo.sysjobs AS j
    LEFT JOIN msdb.dbo.sysjobhistory AS h
        ON j.job_id = h.job_id
       AND h.step_id = 0
)
SELECT
    JobName,
    RunDateTime,
    run_status,
    run_duration,
    message
FROM LastExecution
WHERE RowNumber = 1
ORDER BY JobName;
```

## Jobs That Failed in the Last 24 Hours

```sql
SELECT
    j.name AS JobName,
    msdb.dbo.agent_datetime(h.run_date, h.run_time) AS RunDateTime,
    h.step_id,
    h.step_name,
    h.sql_severity,
    h.sql_message_id,
    h.message
FROM msdb.dbo.sysjobhistory AS h
INNER JOIN msdb.dbo.sysjobs AS j
    ON h.job_id = j.job_id
WHERE h.run_status = 0
  AND msdb.dbo.agent_datetime(h.run_date, h.run_time)
      >= DATEADD(HOUR, -24, SYSDATETIME())
ORDER BY RunDateTime DESC, JobName, h.step_id;
```

Do not limit the analysis to `step_id = 0`. The individual step details often contain the most important information.

## Currently Running Jobs

```sql
SELECT
    j.name AS JobName,
    ja.start_execution_date,
    DATEDIFF(MINUTE, ja.start_execution_date, SYSDATETIME()) AS RunningMinutes,
    ja.last_executed_step_id,
    js.step_name AS LastExecutedStep
FROM msdb.dbo.sysjobactivity AS ja
INNER JOIN msdb.dbo.sysjobs AS j
    ON ja.job_id = j.job_id
LEFT JOIN msdb.dbo.sysjobsteps AS js
    ON ja.job_id = js.job_id
   AND ja.last_executed_step_id = js.step_id
WHERE ja.session_id =
(
    SELECT MAX(session_id)
    FROM msdb.dbo.syssessions
)
AND ja.start_execution_date IS NOT NULL
AND ja.stop_execution_date IS NULL
ORDER BY RunningMinutes DESC;
```

## Disabled Jobs

```sql
SELECT
    name AS JobName,
    date_modified
FROM msdb.dbo.sysjobs
WHERE enabled = 0
ORDER BY name;
```

Every disabled job should have an owner and a documented reason.

## Daily Checklist

1. Did any job fail?
2. Which step failed first?
3. Were there retries?
4. Is the job still running?
5. Is execution time outside the normal range?
6. Did all critical jobs start?
7. Was any job disabled?
8. Are notifications actually working?
9. Is the error isolated or recurring?
10. Does the incident require a documentation update?

## Summary

Daily SQL Server Agent checks should be a repeatable procedure, not just a review of green and red icons.

A calm DBA asks:

> Did the process perform the right work at the right time, and will I find out if it fails to do so next time?
