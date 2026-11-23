---
title: "THREADPOOL Waits: Wenn SQL Server die Worker ausgehen"
date: 2025-10-31
slug: threadpool-waits
tags: [SQLServer, Waits, ThreadPool, Performance, Internals]
draft: false
---

SQL Server ähnelt einem Organismus, der durch Worker-Threads atmet. Jeder Worker ist ein Atemzug; ohne sie erstickt das System.

Wenn `THREADPOOL` in `sys.dm_os_wait_stats` auftaucht, kann SQL Server **nach Luft ringen**. Das ist kein gewöhnlicher Wait: Es kann bedeuten, dass die Engine keine weiteren Worker zuteilen kann, weil die verfügbaren Threads durch parallele Aufgaben, Blocking-Ketten oder andere Arbeit belegt sind.

---

## 🔍 DMV untersuchen

```sql
-- sprawdź obciążenie puli wątków
SELECT scheduler_id, current_tasks_count, runnable_tasks_count, active_workers_count, work_queue_count
FROM sys.dm_os_schedulers
WHERE scheduler_id < 255;
```

📊 **Interpretation:**
- `current_tasks_count` — dem Scheduler zugeordnete Tasks.
- `runnable_tasks_count` — ausführungsbereite Tasks, die auf CPU-Zeit warten.
- `active_workers_count` — aktive Worker des Schedulers.
- `work_queue_count` — Tasks, die auf einen Worker warten.

Wenn sich Runnable Queues auf mehreren Schedulern aufbauen und gleichzeitig `THREADPOOL`-Waits steigen, untersuche sowohl CPU-Scheduling-Druck als auch Worker-Erschöpfung.

---

## ⚙️ Was bedeutet das in der Praxis?

Jede SQL-Server-Instanz besitzt einen **begrenzten Worker-Thread-Pool**, der über die **SOS-Scheduler**-Infrastruktur verwaltet wird. Übersteigt der Bedarf die verfügbaren Worker, müssen neue Tasks **auf einen freien Worker-Thread warten**.

Mögliche Symptome:
- Sitzungen bleiben im Status `SUSPENDED`,
- unerwartet niedrige CPU-Auslastung trotz vieler Verbindungen,
- Blocking-Ketten und massive systemweite Verlangsamung.

---

## 🧠 THREADPOOL-Waits bestätigen

```sql
-- czekające zapytania i typy WAIT
SELECT
    r.session_id,
    r.status,
    r.wait_type,
    r.scheduler_id,
    r.cpu_time,
    r.total_elapsed_time,
    t.text AS QueryText
FROM sys.dm_exec_requests AS r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) AS t
WHERE r.wait_type = 'THREADPOOL';
```

Wenn viele Requests auf `THREADPOOL` warten, untersuche Worker-Nutzung und Blocking-Ketten, um die eigentliche Ursache zu finden.

---

## 🧩 Was kannst du tun?

1️⃣ **Worker-Verbraucher identifizieren:**
- lang laufende parallele Abfragen (auch `CXPACKET` und `CXCONSUMER` können auftreten),
- blockierte Sitzungen mit lang laufenden Transaktionen,
- Schleifen in Jobs, Cursorn oder Systemprozeduren.

2️⃣ **Parallelität prüfen:**
- `max degree of parallelism` (MAXDOP) passend zu Workload und Topologie wählen,
- `cost threshold for parallelism` prüfen; ein zu niedriger Wert kann unnötige Parallelität erzeugen.

3️⃣ **Verbindungen und Jobs prüfen:**
- Connection Management der Anwendungen kontrollieren,
- SQL-Agent-Jobs auf lang laufende oder blockierte Operationen untersuchen.

4️⃣ **Scheduler und Worker überwachen:**
- `sys.dm_os_schedulers` — Warteschlangen und Scheduler-Zustand,
- `sys.dm_os_workers` — Worker-Nutzung,
- `sys.dm_os_waiting_tasks` — aktuelle Waits.

---

## 📈 Schneller Balance-Check

```sql
-- Zlicz ilu workerów działa względem limitu
SELECT COUNT(*) AS ActiveWorkers
FROM sys.dm_os_workers
WHERE state = 'RUNNING';
```

Diese Abfrage zählt nur Worker im Zustand `RUNNING`, nicht alle der Instanz zugeteilten Worker. Zur Diagnose der Erschöpfung sollte die gesamte Worker-Nutzung mit dem konfigurierten oder berechneten Limit verglichen werden.

---

## 💡 SQLManiak: Philosophie der Performance

> „Ein überlastetes System hat vergessen, wie man atmet.“
> — *SQLManiak*

In SQL Server wie im Leben bedeutet **Thread-Balance** auch Energie-Balance. Zu viele gleichzeitige Gedanken können den gesamten Prozess blockieren.

---

#SQLServer #ThreadPool #Waits #Performance #Internals #SQLManiak
