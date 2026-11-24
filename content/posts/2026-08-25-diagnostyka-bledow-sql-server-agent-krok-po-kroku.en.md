---
title: "Why Did a SQL Server Agent Job Fail? Step-by-Step Diagnosis"
date: 2026-08-25
slug: diagnosing-sql-server-agent-job-failures-step-by-step
description: "A systematic approach to diagnosing SQL Server Agent job failures: history, first failed step, execution account, proxy, schedules and logs."
tags: [SQLServer, SQLServerAgent, Troubleshooting, Jobs, DBA]
categories: [SQL Server]
draft: false
---

“The job failed” is not a diagnosis.

Real troubleshooting starts by determining which step failed first, the security context in which it ran, and what changed since the last successful execution.

## Step 1. Find the First Failed Step

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

## Step 2. Inspect the Step Configuration

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

## Step 3. Identify the Security Context

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

A common scenario is:

> The script works when run manually, but fails as a job.

This usually points to differences in the execution account, PowerShell profile, paths, environment variables, or access to a network share.

## Step 4. Check the Job Owner and Schedule

```sql
SELECT
    name AS JobName,
    SUSER_SNAME(owner_sid) AS JobOwner
FROM msdb.dbo.sysjobs
WHERE name = N'TwojJob';
```

A job should not be owned by an arbitrary employee account.

## Step 5. Inspect Logs for the Relevant Subsystem

For T-SQL, analyze job history, the SQL Server Error Log, and Extended Events.

For PowerShell, record the full exception, exit code, and log file.

For SSIS, use SSISDB reports.

For CmdExec, inspect stdout, stderr, the exit code, and the execution account.

## Step 6. Compare Against the Last Successful Run

Check for:

- deployments,
- password changes,
- patching,
- failover,
- DNS changes,
- path changes,
- insufficient disk space,
- permission changes,
- parameter changes.

## Summary

Diagnose job failures layer by layer: execution, step, subsystem, security, schedule, and dependencies.

A calm DBA does not stop at “job failed.”

They identify the first technical root cause and use the incident to improve the process.
