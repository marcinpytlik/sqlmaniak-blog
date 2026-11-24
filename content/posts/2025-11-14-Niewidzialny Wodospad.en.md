---
title: '"The Invisible Waterfall" — Monitoring and Resolving I/O Contention in SQL Server'
date: 2025-11-14
tags:
  - SQL Server
  - SQL Server 2022
  - Monitoring
  - Performance
  - I/O
categories:
  - SQLManiak
draft: false
---

# The Invisible Waterfall — Monitoring and Resolving I/O Contention in SQL Server

Beneath SQL Server's surface is a fascinating choreography of background processes that determine performance. Although Checkpoint, Lazy Writer, and Log Flush perform different tasks, all compete for a critical resource: the I/O subsystem, managed through SQL Server's I/O scheduling mechanisms.

Understanding their interactions is essential. We can make this invisible competition visible with DMVs and Extended Events (XE).

## The Key: Synchronous vs. Asynchronous I/O

To understand the “waterfall,” distinguish two kinds of I/O writes:

**Synchronous I/O (critical):** Primarily Log Flush, associated with the `WRITELOG` wait. A user session performing `COMMIT` may need to wait for its log records to become durable. It is like a telephone call: you wait for the answer.

**Asynchronous I/O (background):** Checkpoint and Lazy Writer can issue background writes. The user session does not necessarily wait for each write to complete. It is like sending an email: delivery happens in the background.

The waterfall problem arises when intense background I/O, such as checkpoint writes, saturates the storage subsystem. Critical log flushes may then suffer increased latency because of contention for shared storage resources.

## What Should We Monitor?

Monitoring these components separately does not provide the full picture. The key is to observe them together.

### 1. Checkpoint

Writes dirty data pages (MDF/NDF), helping bound database recovery work.

**Monitor:** `sys.dm_db_log_stats` (including `log_bytes_to_checkpoint`) and the `checkpoint_end` Extended Event.

**Watch for:** Intense checkpoint activity that saturates I/O and affects other operations, potentially including log writes.

### 2. Lazy Writer

Under buffer-pool memory pressure, Lazy Writer helps free buffers, writing dirty pages when necessary and reclaiming clean ones.

**Monitor:** The Buffer Manager `Lazy writes/sec` performance counter, available through `sys.dm_os_performance_counters`.

**Watch for:** High activity indicating memory pressure and additional background writes.

### 3. Log Flush (Transaction Log Writes)

A critical component of `INSERT`, `UPDATE`, and `DELETE` transactions. A `COMMIT` requiring log durability waits for the corresponding log flush.

**Monitor:** `sys.dm_io_virtual_file_stats` for LDF write latency, and `wait_info` Extended Events for `WRITELOG`.

**Watch for:** High `WRITELOG` latency directly slowing transactional changes.

### 4. I/O Scheduling and Wait Statistics

Waits provide a scoreboard of resource contention.

**Monitor:** `sys.dm_os_wait_stats` for aggregates and `wait_info` XE for current activity.

**Watch for:** `WRITELOG`, `PAGEIOLATCH_SH`/`EX`/`UP`, and `ASYNC_IO_COMPLETION`. Interpret each wait in context rather than assuming they all represent the same bottleneck.

## Why “The Invisible Waterfall”?

One process can trigger a cascade:

1. A large data modification creates thousands of dirty pages.
2. A checkpoint writes those pages using substantial background I/O.
3. The storage subsystem comes under pressure.
4. Other transactions attempt `COMMIT` and require log flushes.
5. Log flush latency rises if the underlying storage resources are shared and saturated.
6. If memory is also under pressure, Lazy Writer may add further writes.

## Other Common Sources of the Waterfall

**Index Rebuild:** Generates substantial reads from the old index, writes to the new index, and transaction-log activity.

**Full/Differential Backup:** Generates large data-file reads that can compete with user queries, including those waiting on `PAGEIOLATCH_SH`.

**Autogrowth:** A sudden MDF or LDF file expansion can pause or delay operations and produce similar symptoms.

## How Can We Demonstrate It?

**Load:** Generate a heavy `INSERT`/`UPDATE` workload in one session. Simultaneously execute small transactions with frequent commits in another.

**Extended Events:** Capture `checkpoint_end`, `log_flush_complete`, and `wait_info`, filtering for `WRITELOG` and relevant `PAGEIOLATCH` waits.

**Analysis:** Compare checkpoint activity and log-flush timing with spikes in `WRITELOG` waits. Remember that `checkpoint_end` marks completion, not the start of a checkpoint.

## Deeper Analysis: Which Queries Suffer? (Query Store)

Once you have established a problem such as high `WRITELOG` waits, identify the affected workload:

1. Open Query Store in SQL Server Management Studio.
2. Select **Top Resource Consuming Queries**.
3. Change the metric from CPU to **Total Wait Time**, where available.
4. Sort the queries and inspect which `UPDATE` or `INSERT` operations spend the most time waiting.

This connects infrastructure-level pressure with the actual queries affected.

## 🎯 How to Resolve or Mitigate the Problem

### 1. Checkpoint: Indirect Checkpoint

Indirect Checkpoint is the default for new databases in modern SQL Server versions and uses `TARGET_RECOVERY_TIME`.

**Effect:** Instead of occasional bursts of dirty-page writes, the engine aims to spread checkpoint I/O more evenly, reducing the risk of storage queue saturation.

**Action:** Review `TARGET_RECOVERY_TIME` (for example, 60 seconds) and validate its behavior against the workload.

### 2. Log Flush: I/O Separation

**Effect:** Placing LDF and MDF/NDF files on genuinely separate storage resources can reduce competition between checkpoint writes and log flushes. Separate drive letters alone do not guarantee physical isolation.

**Action:** Place transaction logs on fast, low-latency storage, ideally isolated from heavy data-file I/O.

### 3. Lazy Writer: Memory Pressure

Excessive Lazy Writer activity is usually a symptom of memory pressure.

**Effect:** Reducing memory pressure means fewer aggressive background writes.

**Action:** Review memory capacity and tune queries or indexes that create unnecessary scans and memory consumption.

## Dashboard (for Example, Grafana)

Visualize these metrics together:

- Log Flush latency and `WRITELOG` waits.
- Data-file write latency from `sys.dm_io_virtual_file_stats`.
- Checkpoint count and duration from `checkpoint_end` XE.
- Lazy Writer activity (`Lazy writes/sec`).
- Key wait statistics.

The value comes from correlating the signals, not interpreting any single metric in isolation.
