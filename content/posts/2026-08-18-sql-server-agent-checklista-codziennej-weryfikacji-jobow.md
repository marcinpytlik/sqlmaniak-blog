---
title: "SQL Server Agent pod kontrolą — checklista codziennej weryfikacji jobów"
date: 2026-08-18T20:00:00+02:00
slug: sql-server-agent-checklista-codziennej-weryfikacji-jobow
description: "Codzienna checklista kontroli jobów SQL Server Agent: błędy, opóźnienia, czas wykonania, wyłączone zadania i brakujące powiadomienia."
tags: [SQLServer, SQLServerAgent, Jobs, DBA, Monitoring, Checklist]
categories: [SQL Server]
draft: false
---

Zielona ikona przy jobie SQL Server Agent nie wystarcza, aby uznać proces za bezpieczny.

Job może zakończyć się sukcesem, mimo że nie wykonał wszystkich kroków, uruchomił się z opóźnieniem albo działał znacznie dłużej niż zazwyczaj.

## Co powinna wykrywać codzienna kontrola?

- joby zakończone błędem,
- joby anulowane,
- joby uruchomione z opóźnieniem,
- joby, które nadal działają,
- nietypowy czas wykonania,
- joby wyłączone,
- joby bez harmonogramu,
- joby bez powiadomienia.

## Ostatni status wszystkich jobów

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

## Joby zakończone błędem w ostatnich 24 godzinach

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

Nie ograniczaj analizy tylko do `step_id = 0`. Szczegół kroku zwykle zawiera najważniejszą informację.

## Aktualnie działające joby

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

## Joby wyłączone

```sql
SELECT
    name AS JobName,
    date_modified
FROM msdb.dbo.sysjobs
WHERE enabled = 0
ORDER BY name;
```

Każdy wyłączony job powinien mieć właściciela i uzasadnienie.

## Codzienna checklista

1. Czy którykolwiek job zakończył się błędem?
2. Jaki był pierwszy błędny krok?
3. Czy wystąpiły retry?
4. Czy job nadal działa?
5. Czy czas wykonania odbiega od normy?
6. Czy wszystkie krytyczne joby wystartowały?
7. Czy któryś job został wyłączony?
8. Czy powiadomienia rzeczywiście działają?
9. Czy błąd jest jednorazowy, czy powtarzalny?
10. Czy zdarzenie wymaga aktualizacji dokumentacji?

## Podsumowanie

Codzienna kontrola SQL Server Agent powinna być powtarzalną procedurą, a nie przeglądaniem zielonych i czerwonych ikon.

Spokojny DBA pyta:

> Czy proces wykonał właściwą pracę, we właściwym czasie i czy dowiem się, gdy następnym razem tego nie zrobi?
