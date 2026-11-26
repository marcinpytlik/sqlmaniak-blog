---
title: "Blocking, Lock Waits und Timeouts — gemeinsam interpretieren"
date: 2026-11-24T08:00:00+01:00
slug: blocking-lock-waits-timeouts
description: "Blocking, Lock Waits und Lock Timeouts in SQL Server korrelieren, um normale Sperren von echten Vorfällen zu unterscheiden."
tags: [SQLServer, Blocking, Locks, Performance, DBA]
categories: [SQL Server]
draft: false
---

Blocking gehört zum normalen Betrieb von SQL Server.

Das Problem ist nicht, dass eine Session auf eine andere wartet. Kritisch wird es, wenn Wartezeit und Systemauswirkungen die akzeptablen Grenzen überschreiten.

## Aktuelles Blocking

```sql
SELECT
    r.session_id,
    r.blocking_session_id,
    DB_NAME(r.database_id) AS DatabaseName,
    r.wait_type,
    r.wait_time,
    r.wait_resource
FROM sys.dm_exec_requests AS r
WHERE r.blocking_session_id <> 0
ORDER BY r.wait_time DESC;
```

Dies zeigt die momentane Situation, aber nicht, wie häufig das Problem auftritt.

## Lock Waits

```sql
SELECT
    wait_type,
    waiting_tasks_count,
    wait_time_ms
FROM sys.dm_os_wait_stats
WHERE wait_type LIKE N'LCK_M_%'
ORDER BY wait_time_ms DESC;
```

Am aussagekräftigsten ist die Veränderung (Delta) innerhalb eines definierten Zeitintervalls.

## Lock Timeout

```sql
SET LOCK_TIMEOUT 5000;
```

Die Anforderung schlägt fehl, wenn sie fünf Sekunden auf eine Sperre gewartet hat. Allein das Monitoring aktiver Blockierungen zeigt daher nicht immer die gesamten Auswirkungen auf die Anwendung.

## Drei Signale korrelieren

- Dauer und Anzahl aktiver Blockierungen.
- Zunahme der `LCK_M_*`-Waits.
- Anzahl der Timeouts in der Anwendung oder in Extended Events.

## Sessions nicht automatisch beenden

`KILL` kann ein Symptom beseitigen und gleichzeitig einen teuren Rollback auslösen. Prüfe zuerst die Transaktion und die geschäftlichen Folgen.

## Zusammenfassung

Ein besonnener DBA alarmiert nicht bei jeder Sperre.

Er alarmiert bei Blocking, das messbare Auswirkungen auf System und Benutzer hat.
