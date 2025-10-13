---
title: "Threadpool Waits – gdy zabraknie wątków"
date: 2025-10-31
slug: threadpool-waits
tags: [SQLServer, Waits, ThreadPool, Performance, Internals]
draft: false
---

SQL Server jest jak organizm oddychający wątkami. Każdy worker to oddech – bez nich system się dusi.  
Gdy zobaczysz `THREADPOOL` w `sys.dm_os_wait_stats`, wiesz, że SQL Server walczy o tlen.

### 🔍 Zajrzyj w DMV
```sql
-- sprawdź obciążenie puli wątków
SELECT scheduler_id, current_tasks_count, runnable_tasks_count, active_workers_count, work_queue_count
FROM sys.dm_os_schedulers
WHERE scheduler_id < 255;
```

> „Przeciążony system to system, który zapomniał oddychać.” — SQLManiak
