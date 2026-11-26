---
title: "EF Core through the eyes of a DBA – a sleeping session, an exhausted pool and an open transaction"
date: 2026-11-27T08:00:00+01:00
draft: false
translationKey: "ef-core-connection-pool-exhaustion"
description: "Five experiments with EF Core 10, SqlClient and SQL Server 2022: pool exhaustion, blocking and session reset."
categories: ["EF Core through the eyes of a DBA", "SQL Server"]
tags: ["EF Core 10", "SQL Server 2022", "Connection Pooling", "Microsoft.Data.SqlClient", "Extended Events", "DMV", "Blocking"]
---

## SQL Server responds, but the application does not work

Imagine a production incident: users cannot access an application that keeps reporting timeouts. The DBA checks active requests, blocking and open transactions. Application sessions are `sleeping`, and the database engine responds to diagnostic queries. Where should we look for the cause?

Perhaps we are looking on the wrong side of the architecture. This laboratory was inspired by Hannah Vernon's article [Connection Pool Exhaustion](https://www.sqlserverscience.com/troubleshooting/connection-pool-exhaustion/). I wanted to reproduce some of her observations using a modern .NET 10 stack and extend the experiment with SqlClient telemetry, DMVs, Extended Events and a controlled blocking test.

## 1. Three different lifecycles

The lifetime of a `DbContext`, a logical connection and a physical SQL Server session are three different things. Connection pooling allows physical connections to be reused instead of establishing transport and authenticating the user every time. `Close()` or `Dispose()` normally returns a connection to the pool when pooling is enabled and the connection is reusable.

A `sleeping` session has no currently executing request; its status says nothing about whether the connection is available in the pool. SqlClient manages pools inside the application process. SQL Server does not know how many free slots those pools contain. DbContext pooling is distinct from connection pooling.

## 2. Environment and methodology

| Component | Version |
|---|---|
| SQL Server | 2022 Developer CU28, 16.0.4325.4 |
| Container OS | Ubuntu 22.04.5 LTS |
| .NET | 10 |
| EF Core | 10.0.15 |
| Microsoft.Data.SqlClient | 6.1.7 (assembly 6.0.0.0) |
| SNI Runtime | 6.0.3 |
| dotnet-counters | 10.0.750501 |
| Environment | Docker Desktop, PowerShell 7 |
| Measurement date | 2026-11-26 |

I used `tempdb` in an isolated container and deliberately configured a small connection pool. This is an experimental configuration, not a production recommendation.

```csharp
var cs = new SqlConnectionStringBuilder
{
    DataSource = "127.0.0.1,15468",
    InitialCatalog = "tempdb",
    UserID = "sa",
    Password = password,
    TrustServerCertificate = true,
    ApplicationName = "SQLManiak.Lab68",
    MaxPoolSize = 3,
    ConnectTimeout = 5,
    ConnectRetryCount = 0,
    Pooling = true
}.ConnectionString;
```

Five scenarios: A – baseline, B – pool exhaustion, C – transaction after Dispose, D – blocking after Dispose, E – explicit rollback. I collect data at three levels: application, SqlClient and SQL Server. CSV timestamps recorded in local CET are converted to UTC.

## 3. Experiment A – Baseline

Each of ten sequential operations creates a new context:

```csharp
await using var db = new LabContext(options);
var spid = await db.Database
    .SqlQueryRaw<int>("SELECT CAST(@@SPID AS int) AS Value")
    .SingleAsync();
```

| Operation | SPID | Time (ms) |
|---:|---:|---:|
| 1 | 53 | 590 |
| 2 | 53 | 25 |
| 3 | 53 | 83 |
| 4 | 53 | 2 |
| 5 | 53 | 2 |
| 6 | 53 | 2 |
| 7 | 53 | 2 |
| 8 | 53 | 1 |
| 9 | 53 | 2 |
| 10 | 53 | 2 |

![Baseline operation timings](/images/lab68/01-baseline.svg)

*Figure 1. Actual measurements, logarithmic scale.*

All operations succeeded, with a median of 2 ms. The same SPID throughout the sequence is consistent with session reuse. The initial 590 ms may include EF Core initialization, JIT compilation and connection establishment; it is not an isolated measurement of login overhead.

## 4. Experiment B – Connection Pool Exhaustion

Three contexts explicitly open connections (`await db.Database.OpenConnectionAsync();`) and retain them after their queries finish. The fourth acquisition attempt must wait for an available pool slot.

In one run, DMVs showed SPIDs 60, 62 and 63: all `sleeping`, `open_transaction_count=0`, with no active requests or blocking in the samples. Nevertheless, the application raised an `InvalidOperationException` indicating that the time limit elapsed before a connection could be obtained from the pool.

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Connect Timeout (ms) | 5000 | 5000 |
| Observed timeout (ms) | 5021 | 5015 |
| Recovery (ms) | 5 | 6 |
| Recovery SPID | 63 | 70 |

After releasing the three contexts, the next query succeeded without restarting the application or SQL Server. Waiting for a pool slot does not necessarily create a server-side request. This is not a SQL command execution timeout.

### EventCounters – client-side evidence

Provider: `Microsoft.Data.SqlClient.EventSource`. I collected 60 samples of four counters (240 values). In the repeat of B, the held SPIDs were 68, 69 and 70.

| UTC interval (inclusive) | Samples | Active | Ready | Pooled | Pools |
|---|---:|---:|---:|---:|---:|
| 21:20:05–21:20:54 | 50 | 3 | 0 | 3 | 1 |
| 21:20:55–21:21:04 | 10 | 0 | 3 | 3 | 1 |

The timeout occurred at 21:20:40.081 UTC and the connections were released at 21:20:55.102 UTC. Recovery took 6 ms; its brief checkout was not captured by the one-second samples.

![Pool exhaustion and recovery](/images/lab68/02-pool-exhaustion.svg)

*Figure 2. Actual EventCounters samples, UTC.*

The number of pooled connections remained three. Availability changed from zero to three. Application-process telemetry directly reveals what SQL Server session status alone cannot tell us.

## 5. Experiment C – Transaction after Dispose

What happens when I start a transaction directly through T-SQL and then dispose of the connection object?

```csharp
await using (var c = new SqlConnection(cs))
{
    await c.OpenAsync();
    await using var cmd = c.CreateCommand();
    cmd.CommandText = "BEGIN TRANSACTION; SELECT @@SPID;";
    Console.WriteLine(await cmd.ExecuteScalarAsync());
}
```

I deliberately issue neither COMMIT nor ROLLBACK. I observe the session for approximately 30 seconds, then acquire a connection again.

| UTC | Observation |
|---|---|
| 21:03:32.273 | connect_time of SPID 53 |
| 21:03:32.363 | Transaction 13578 begins |
| 21:03:33.400 | sleeping, open_transaction_count=1 |
| 21:04:02.002 | Last sample with active transaction |
| 21:04:02.922 | Next application operation succeeds |
| 21:04:03.101 | First sample with open_transaction_count=0 |

![Transaction after Dispose](/images/lab68/03-transaction-after-dispose.svg)

*Figure 3. DMV samples; the transition is bounded by the sampling interval.*

The transaction was active (state 2) in 27 samples and absent in the following 14. SPID and connect_time remained unchanged. In this configuration the T-SQL transaction survived Dispose and disappeared on connection reuse. No data modification was performed here; I tested blocking separately.

## 6. Experiment D – Blocking after Dispose

I create a uniquely named table in `tempdb` with an initial value of `V=0`. Illustrative T-SQL for the owner session:

```sql
BEGIN TRANSACTION;
UPDATE dbo.Lab68_Test SET V = 1 WHERE Id = 1;
```

After Dispose, a second session using an independent, nonpooled connection executes:

```sql
SELECT V FROM dbo.Lab68_Test WITH (READCOMMITTEDLOCK)
WHERE Id = 1;
```

The hint forces a locking read even when RCSI is enabled. The actual code generates the table name dynamically.

| Parameter | Owner | Observer |
|---|---|---|
| SPID | 60 | 59 |
| Session status | sleeping | running |
| Request status | NULL | suspended |
| Open transactions | 1 | 0 |
| Wait type | NULL | LCK_M_S |
| Blocking session ID | NULL | 60 |

Nine consecutive samples showed this blocking relationship. After 10 seconds, the observer's read was still pending. Reusing SPID 60 returned `@@TRANCOUNT=0`, and the observer read the original value of 0. This confirms that the modification was rolled back and blocking ceased.

![Blocking chain](/images/lab68/04-blocking-chain.svg)

*Figure 4. Diagram of the mechanism supported by measurements.*

## 7. Extended Events – session reset

The `login`, `logout`, `rpc_completed` and `sql_batch_completed` events reconstructed the owner's sequence:

| UTC | Event |
|---|---|
| 21:13:50.678 | login, is_cached=false |
| 21:13:50.681 | SELECT @@SPID |
| 21:13:50.693 | BEGIN TRANSACTION + UPDATE |
| 21:13:50.698 | Dispose in application log |
| 21:14:00.711 | logout, is_cached=true |
| 21:14:00.711 | rpc_completed: sp_reset_connection |
| 21:14:00.711 | login, is_cached=true |
| 21:14:00.712 | SELECT @@SPID, @@TRANCOUNT |
| 21:14:00.715 | Observer read completed (application log) |

XE reported a duration of 281 µs for the SPID 60 reset, with result OK. The ring buffer reported eight events, droppedCount=0 and truncated=0. The observer was outside the XE filter; its completion is evidenced by the application log. Cached login/logout events do not indicate a new physical connection here.

The reset on reuse, disappearance of the transaction and read of value 0 form consistent evidence for the mechanism. We did not observe a reset at the earlier Dispose.

## 8. Experiment E – Explicit Rollback

The control uses the SqlClient transaction API and explicitly rolls back before disposing of the connection:

```csharp
await using var tx = (SqlTransaction)await owner.BeginTransactionAsync();
// UPDATE with tx assigned to SqlCommand.Transaction
await tx.RollbackAsync();
```

| Parameter | D – Blocking | E – Rollback |
|---|---|---|
| UPDATE | Yes | Yes |
| Explicit rollback | No | Yes |
| Read pending after 10 s | Yes | No |
| LCK_M_* in samples | LCK_M_S | None |
| TRANCOUNT after reuse | 0 | 0 |
| Value read | 0 | 0 |

The original elapsed values of 10014 and 10012 ms included the deliberate observation window. They are not comparable isolated SELECT timings. The timing code has been corrected, but a rerun of the correction remains pending. The control changes both the transaction initiation API and the explicit rollback, so it does not isolate their individual effects.

## 9. Production diagnostics

```sql
SELECT SYSUTCDATETIME() AS ObservationUTC,
       s.session_id, s.host_name, s.program_name, s.login_name,
       s.status AS SessionStatus, s.open_transaction_count,
       r.status AS RequestStatus, r.wait_type, r.wait_time,
       r.blocking_session_id, c.connect_time,
       s.last_request_start_time, s.last_request_end_time
FROM sys.dm_exec_sessions AS s
LEFT JOIN sys.dm_exec_requests AS r ON s.session_id = r.session_id
LEFT JOIN sys.dm_exec_connections AS c ON s.session_id = c.session_id
WHERE s.is_user_process = 1
ORDER BY s.open_transaction_count DESC, s.session_id;
```

To identify sleeping sessions with open transactions:

```sql
SELECT session_id, host_name, program_name, login_name,
       open_transaction_count, last_request_end_time,
       DATEDIFF(SECOND, last_request_end_time, SYSDATETIME()) AS IdleSeconds
FROM sys.dm_exec_sessions
WHERE is_user_process = 1 AND status = N'sleeping'
  AND open_transaction_count > 0
ORDER BY IdleSeconds DESC;
```

Appropriate DMV permissions are required (typically VIEW SERVER PERFORMANCE STATE in SQL Server 2022). Finding such a session is not an automatic reason to issue KILL. First establish the owner, transaction age, blocked resources and potential rollback impact.

Open transactions can cause blocking, delay transaction log space reuse and retain row versions in relevant isolation scenarios. Prolonged blocking can, in turn, increase connection holding times and exhaust the pool. However, I did not measure log growth, Version Store growth or this cascade in Lab 68.

## 10. Recommendations for .NET developers and DBAs

Open connections as late as practical and release them as early as practical. Do not retain them during unrelated HTTP operations. Manage transactions explicitly, with COMMIT on success and appropriate rollback on failure; prefer EF Core or ADO.NET transaction APIs. Do not rely on a future session reset as a cleanup strategy.

Increasing Max Pool Size may be justified by workload requirements, but it does not repair an incorrect connection lifecycle. Monitor Active/Ready/Pooled counts, pool count, acquisition latency, exceptions and transaction duration. Correlate them with DMVs and XE. DbContext pooling does not replace SqlClient pool management.

![Three diagnostic perspectives](/images/lab68/05-diagnostic-perspectives.svg)

*Figure 5. Diagnostic methodology – conceptual diagram.*

## 11. Reproduction

Code: [SQLManiak Lab 68 – PR #146](https://github.com/marcinpytlik/SQLManiak/pull/146). In an isolated lab with Docker, .NET 10, PowerShell 7, sqlcmd and dotnet-counters:

```powershell
cd labs\68_ConnectionPoolExhaustion
$env:LAB_PASSWORD = Read-Host "SA password" -MaskInput
docker compose up -d
# Wait until SQL Server is ready before running the tests.
.\Invoke-Lab68.ps1 -Counters -XE
# Selected scenarios:
.\Invoke-Lab68.ps1 -Scenario exhaustion -Counters -XE
.\Invoke-Lab68.ps1 -Scenario blocking,rollback -XE
```

The script saves application logs, DMVs, XE, counters and package versions in a separate results directory. Afterwards run `docker compose down` and `Remove-Item Env:\LAB_PASSWORD`. SA and TrustServerCertificate are used only in the laboratory environment.

## 12. Limitations and conclusion

The experiments ran locally with a small pool, a specific provider and a forced locking read. Sampling is not continuous tracing; the observations cannot automatically be generalized to all library versions or transaction APIs. This is a mechanism investigation, not a throughput benchmark.

Five observations: successive DbContexts can share a physical session; sleeping does not mean a free connection; pool exhaustion need not generate a SQL request; a T-SQL transaction can survive Dispose; a sleeping session can block other users. In the tested configuration, XE confirmed reset on reuse and EventCounters showed recovery of pool availability.

A modern DBA needs to understand not only what happens inside the database, but also what happens between the application and the database.

**SQLManiak – less theory, more evidence.**

## Resources

- [Hannah Vernon – Connection Pool Exhaustion](https://www.sqlserverscience.com/troubleshooting/connection-pool-exhaustion/)
- [SQLManiak – Lab 68](https://github.com/marcinpytlik/SQLManiak/pull/146)
- [Microsoft Learn – SQL Server connection pooling](https://learn.microsoft.com/en-us/sql/connect/ado-net/sql-server-connection-pooling)
- [Microsoft Learn – dotnet-counters](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters)
