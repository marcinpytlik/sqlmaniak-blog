---
title: "Why the transaction log does not shrink and what to do about it"
date: "2025-10-04"
slug: "dlaczego-log-nie-maleje-po-shrink-en"
draft: false
description: "A complete guide to log-shrink obstacles: VLFs, open transactions, missing log backups and replication."
tags: ["Transaction Log","VLF","Backup"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/dlaczego-log-nie-maleje-po-shrink.png"

---

## Introduction
“I ran SHRINK and nothing happened.” A familiar story. A log file cannot shrink if an *active portion of the log* sits near the end of the file or transactions remain open. Let's diagnose it step by step.

## Quick diagnosis
```sql
-- Aktywny log, VLF-y
DBCC LOGINFO;   -- w nowszych wersjach: sys.dm_db_log_info(DB_ID())

SELECT vlf_sequence_number, vlf_active, file_id FROM sys.dm_db_log_info(DB_ID())
ORDER BY vlf_sequence_number;
```

### Main shrink blockers
- Open or long-running transactions, including a forgotten implicit transaction in SSMS.
- No log backup chain: FULL recovery without `BACKUP LOG`.
- Replication, CDC or log shipping retaining log records.
- Too many small VLFs caused by tiny FILEGROWTH increments.

## Reclaiming space
1. **Take a log backup** in FULL or BULK_LOGGED recovery.
2. **Identify and resolve long-running transactions**:
```sql
SELECT s.session_id, r.start_time, r.status, r.command, r.wait_type, s.login_name, s.host_name
FROM sys.dm_exec_requests r
JOIN sys.dm_exec_sessions s ON s.session_id=r.session_id
WHERE r.database_id = DB_ID();
```
3. **Pause replication or CDC only if operationally safe** during the maintenance window.
4. **Perform a controlled shrink**:
```sql
USE MyDb;
DBCC SHRINKFILE (MyDb_log, 102400); -- target w MB
```
5. **Set a sensible FILEGROWTH and baseline log size**, for example 64–128 GB in a heavy OLTP environment, based on measurements.

## VLF housekeeping
- Check the VLF count; aim for hundreds rather than tens of thousands.
- Consider a planned BACKUP LOG → SHRINKFILE → single-step growth cycle.
```sql
-- Przykład: ustaw 64GB i growth 4GB
DBCC SHRINKFILE (MyDb_log, 1024); -- tymczasowe przycięcie
ALTER DATABASE MyDb MODIFY FILE (NAME=MyDb_log, SIZE=65536MB, FILEGROWTH=4096MB);
```

## Verification and monitoring
- Check `sys.dm_db_log_space_usage` and `sys.dm_db_log_stats(DB_ID())`.
- In Grafana, monitor log utilization, VLF count and autogrowth frequency.

## Anti-patterns
- Nightly shrinking causes unnecessary regrowth and can harm performance.
- Very small FILEGROWTH increments create excessive VLFs.
- FULL recovery without a log backup strategy.
