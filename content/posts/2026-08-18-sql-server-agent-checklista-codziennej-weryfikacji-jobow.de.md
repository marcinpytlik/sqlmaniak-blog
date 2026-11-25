---
title: "SQL Server Agent unter Kontrolle — Checkliste für die tägliche Jobprüfung"
date: 2026-08-18
slug: sql-server-agent-taegliche-jobpruefung-checkliste
description: "Tägliche SQL-Server-Agent-Checkliste: Fehler, Verzögerungen, Laufzeiten, deaktivierte Jobs und fehlende Benachrichtigungen."
tags: [SQLServer, SQLServerAgent, Jobs, DBA, Monitoring, Checklist]
categories: [SQL Server]
draft: false
---

Ein grünes Symbol neben einem SQL-Server-Agent-Job reicht nicht aus, um einen Prozess als sicher einzustufen.

Ein Job kann erfolgreich beendet werden, obwohl nicht alle Schritte ausgeführt wurden, er verspätet startete oder wesentlich länger als üblich lief.

## Was sollte die tägliche Kontrolle erkennen?

- fehlgeschlagene Jobs,
- abgebrochene Jobs,
- verspätet gestartete Jobs,
- noch laufende Jobs,
- ungewöhnliche Laufzeiten,
- deaktivierte Jobs,
- Jobs ohne Zeitplan,
- Jobs ohne Benachrichtigung.

## Letzter Status aller Jobs

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

## In den letzten 24 Stunden fehlgeschlagene Jobs

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

Beschränke die Analyse nicht auf `step_id = 0`. Die Details der einzelnen Schritte enthalten oft die entscheidenden Informationen.

## Aktuell laufende Jobs

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

## Deaktivierte Jobs

```sql
SELECT
    name AS JobName,
    date_modified
FROM msdb.dbo.sysjobs
WHERE enabled = 0
ORDER BY name;
```

Für jeden deaktivierten Job sollten ein Verantwortlicher und eine dokumentierte Begründung existieren.

## Tägliche Checkliste

1. Ist ein Job fehlgeschlagen?
2. Welcher Schritt ist zuerst fehlgeschlagen?
3. Gab es Wiederholungsversuche?
4. Läuft der Job noch?
5. Weicht die Laufzeit vom Normalbereich ab?
6. Sind alle kritischen Jobs gestartet?
7. Wurde ein Job deaktiviert?
8. Funktionieren die Benachrichtigungen tatsächlich?
9. Handelt es sich um einen einmaligen oder wiederkehrenden Fehler?
10. Muss die Dokumentation nach dem Vorfall aktualisiert werden?

## Zusammenfassung

Die tägliche SQL-Server-Agent-Kontrolle sollte ein wiederholbares Verfahren sein, nicht bloß eine Betrachtung grüner und roter Symbole.

Ein besonnener DBA fragt:

> Hat der Prozess die richtige Arbeit zur richtigen Zeit erledigt, und werde ich erfahren, wenn das beim nächsten Mal nicht der Fall ist?
