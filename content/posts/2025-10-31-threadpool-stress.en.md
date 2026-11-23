---
title: "THREADPOOL Waits: When SQL Server Runs Out of Workers"
date: 2025-10-31
slug: threadpool-waits
tags: [SQLServer, Waits, ThreadPool, Performance, Internals]
draft: false
---

SQL Server is like an organism that breathes through worker threads. Each worker is a breath; without them, the system suffocates.

When you see `THREADPOOL` in `sys.dm_os_wait_stats`, SQL Server may be **struggling for air**. This is not an ordinary wait: it can indicate that the engine cannot allocate additional workers because available threads are occupied by parallel tasks, blocking chains, or other work.

---

## 🔍 Inspect the DMV

```sql
-- sprawdź obciążenie puli wątków
SELECT scheduler_id, current_tasks_count, runnable_tasks_count, active_workers_count, work_queue_count
FROM sys.dm_os_schedulers
WHERE scheduler_id < 255;
```

📊 **Interpretation:**
- `current_tasks_count` — tasks associated with the scheduler.
- `runnable_tasks_count` — tasks ready to run and waiting for CPU scheduling.
- `active_workers_count` — active workers on the scheduler.
- `work_queue_count` — tasks queued for a worker.

If runnable queues build across schedulers while `THREADPOOL` waits increase, investigate both CPU scheduling pressure and worker exhaustion.

---

## ⚙️ What it means in practice

Each SQL Server instance has a **finite worker-thread pool**, managed by the **SOS Scheduler** infrastructure. When demand exceeds the available workers, new tasks must **wait for a worker thread**.

Symptoms may include:
- sessions remaining `SUSPENDED`,
- unexpectedly low CPU use despite many connections,
- blocking chains and severe system-wide slowdowns.

---

## 🧠 How to confirm THREADPOOL waits

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

If many requests are waiting on `THREADPOOL`, examine worker usage and blocking chains to determine the underlying cause.

---

## 🧩 What can you do?

1️⃣ **Identify worker consumers:**
- long-running parallel queries (`CXPACKET`, `CXCONSUMER` may also be present),
- blocked sessions with long-lived transactions,
- looping jobs, cursors, or system procedures.

2️⃣ **Review parallelism:**
- choose an appropriate `max degree of parallelism` (MAXDOP) based on workload and topology,
- review `cost threshold for parallelism`; an overly low threshold can create unnecessary parallel work.

3️⃣ **Review connections and jobs:**
- check application connection management,
- inspect SQL Agent jobs for long-running or blocked operations.

4️⃣ **Monitor schedulers and workers:**
- `sys.dm_os_schedulers` — queues and scheduler state,
- `sys.dm_os_workers` — worker usage,
- `sys.dm_os_waiting_tasks` — current waits.

---

## 📈 Quick balance check

```sql
-- Zlicz ilu workerów działa względem limitu
SELECT COUNT(*) AS ActiveWorkers
FROM sys.dm_os_workers
WHERE state = 'RUNNING';
```

This counts workers currently in the `RUNNING` state, not every worker allocated to the instance. For diagnosing exhaustion, compare total worker usage with the configured or calculated limit.

---

## 💡 SQLManiak: A philosophy of performance

> “An overloaded system is a system that has forgotten how to breathe.”
> — *SQLManiak*

In SQL Server and in life, **thread balance** is energy balance. Too many simultaneous thoughts can block the whole process.

---

#SQLServer #ThreadPool #Waits #Performance #Internals #SQLManiak
