---
title: "EF Core Through a DBA's Eyes: 101 Queries vs One. What Does Query Store Really Reveal?"
date: 2026-11-22T12:00:00+01:00
slug: "ef-core-n-plus-one-include-projection-split-query-query-store"
description: "A controlled .NET 10, EF Core 10, and SQL Server 2022 experiment comparing N+1, Include, Projection, and SplitQuery: application time, SQL CPU, logical reads, and the JIT/AOT question."
category: "Relational Renaissance"
tags:
  - SQL Server
  - EF Core
  - .NET 10
  - Query Store
  - N+1
  - performance tuning
  - ORM
draft: true
---

# EF Core Through a DBA's Eyes: 101 Queries vs One. What Does Query Store Really Reveal?

**Is N+1 only a problem of too many SQL statements? And if DTO projection is the fastest approach from the application's perspective, does it necessarily consume the least CPU on SQL Server?**

Rather than rely on intuition, I built a repeatable lab using **.NET 10, EF Core 10, and SQL Server 2022**. I implemented four approaches to retrieving the same data, measured their execution time in the application, and then compared Query Store counter deltas.

The results highlight two things: N+1 has a measurable cost, but **the shortest application time does not necessarily mean the least expensive SQL Server workload**.

Source code, containers, and scripts:

**[WWSI_CSharp — Demo 67: EF Core Performance Lab](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab)**

## Lab Environment and Scope

Performance numbers only make sense in the context of the machine on which they were collected. In my [earlier article on JIT, ReadyToRun, and Native AOT](https://sqlmaniak.blog/posts/dotnet10-efcore10-sqlserver-startup-jit-r2r-native-aot/), I documented the following workstation configuration:

| Component | Configuration documented for the earlier lab |
|---|---|
| Host operating system | Microsoft Windows 11 Pro, version 10.0.26300 (build 26300), x64 |
| Processor | Intel Core i5-1035G1 @ 1.00 GHz |
| Physical cores / logical processors | 4 / 8 |
| Host RAM | 7.81 GiB |
| .NET SDK | 10.0.403 |
| .NET / EF Core (earlier test) | 10.0.14 / 10.0.14 |
| PowerShell (earlier test) | 7.6.9 |
| Docker Client / Engine (earlier test) | 29.9.2 / 29.9.2 |
| Container environment (earlier test) | Linux, 8 CPUs; approximately 3.73 GiB reported by `docker info` |

**I ran both experiments on the same physical machine, using the same processor, RAM, and operating system.** I have confirmed these hardware details for both labs. Tool versions and individual container resources are separate variables, however; without a fresh reading, I do not assume they remained unchanged.

For **EF Core Performance Lab 67**, the reproducible configuration recorded in the [demo repository](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab) is:

| Component | Demo 67 configuration |
|---|---|
| Application | ASP.NET Core / .NET 10, EF Core 10, API built in Docker |
| Database engine | SQL Server 2022 Developer, Linux container |
| SQL Server image | `mcr.microsoft.com/mssql/server:2022-latest` |
| SQL endpoint on host | `127.0.0.1:14367` |
| API endpoint on host | `127.0.0.1:5087` |
| Database | `EfPerformanceLab` |
| Test data | 100 orders, 1,000 order items (10 per order) |
| Query Store | `READ_WRITE`, `QUERY_CAPTURE_MODE = ALL` |
| Test series | 10 calls per strategy, separate BEFORE/AFTER snapshots |
| Run identifier | `fb6e09ce`, November 22, 2026 |

The earlier study used a **different SQL Server container**, `sql2022-startuplab`, exposed on port **14333**. For that container I verified **SQL Server 2022 RTM-CU27, 16.0.4295.3**, and a **4 GiB** memory limit. **I do not automatically apply either parameter to Demo 67**: its `2022-latest` image tag is mutable, and its Compose file does not declare a SQL Server memory limit.

For better reproducibility, the actual parameters of the running Demo 67 container can be captured with:

```powershell
docker compose exec -T sql bash -c 'export SQLCMDPASSWORD="$MSSQL_SA_PASSWORD"; /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -d master -h -1 -W -Q "SET NOCOUNT ON; SELECT @@VERSION;"'
docker compose ps
docker version
docker info
```

Using the same workstation helps place both experiments in context, while the SQL container configuration must still be documented separately.

## Same Data, Four Strategies

My demo database contains 100 orders, each with 10 items: **100 rows in Orders and 1,000 rows in OrderItems**. Every endpoint returns the same DTO structure, the same records, and the same item ordering.

| Strategy | Mechanism | SQL statements per request |
|---|---|---:|
| **N+1** | One SELECT for orders, then a separate SELECT for items in a loop | **101** |
| **Include** | `Include(x => x.Items)` + `AsSingleQuery()` | **1** |
| **Projection** | `Select()` directly into DTOs + `AsSingleQuery()` | **1** |
| **SplitQuery** | `Include(x => x.Items)` + `AsSplitQuery()` | **2** |

All variants use `AsNoTracking()`. I deliberately implement N+1 with an explicit loop, without lazy-loading proxies, to make the effect deterministic: retrieve the parent records once, then retrieve each parent's children individually.

Here is a simplified version of the anti-pattern:

```csharp
var orders = await db.Orders
    .AsNoTracking()
    .OrderBy(o => o.Id)
    .Take(100)
    .ToListAsync();

foreach (var order in orders)
{
    var items = await db.OrderItems
        .AsNoTracking()
        .Where(i => i.OrderId == order.Id)
        .ToListAsync();

    // Build an order DTO with its items.
}
```

**This is not production guidance.** It is intentionally inefficient code designed to make the cost measurable.

For comparison, `Include` retrieves related data with a single SQL statement:

```csharp
var orders = await db.Orders
    .AsNoTracking()
    .AsSingleQuery()
    .OrderBy(o => o.Id)
    .Take(100)
    .Include(o => o.Items)
    .ToListAsync();
```

The projection variant selects directly into DTOs, while `AsSplitQuery()` splits retrieval of the parent and its single collection into two SQL statements. In the actual demo, all approaches produce **the same response contract**.

## How I Measured Without Comparing Unrelated Numbers

I first verified data correctness and counted SQL commands using `DbCommandInterceptor`. Only then did I start benchmarking.

The final automated run used:

- **10 repetitions per strategy**, or 40 measured EF Core operations;
- warm-up before the measured series;
- independent series for N+1, Include, Projection, and SplitQuery;
- a Query Store **BEFORE** snapshot, a benchmark, and an **AFTER** snapshot for each series;
- verification that Query Store recorded the expected number of SQL statement executions.

That last check matters. Earlier Query Store data showed, for example, 4,271 executions of the statement retrieving order items, but they did not all belong to a single controlled benchmark interval. Such historical totals **must not** be compared directly with ten API calls to a different endpoint.

While developing the snapshots, I found that the query text exposed by Query Store in this environment did not let me reliably identify statements by their `TagWith()` comments. Filtering for `EFPLAB:` returned zero matches before the test and one afterward; that match was the diagnostic statement itself, which contained the marker as a literal. I did not establish why the comments were unavailable in the expected form. Instead, I identified characteristic fragments of the generated SQL and measured each strategy in isolation.

It is a useful DBA reminder: **before comparing diagnostic counters, check that they refer to the same workload and measurement window**.

## EF Core Results: 119.83 ms vs 5.11 ms

In the controlled run, these were the medians for application-side operations:

| Strategy | Median EF Core time | SQL statements |
|---|---:|---:|
| N+1 | **119.83 ms** | 101 |
| Include | **6.01 ms** | 1 |
| Projection | **5.11 ms** | 1 |
| SplitQuery | **5.23 ms** | 2 |

In this specific run:

- Include had a median about **19.9 times lower** than N+1;
- Projection was about **23.5 times lower**;
- SplitQuery was about **22.9 times lower**.

Does that make Projection universally best? **No.** The differences among the three faster approaches are small; assessing them reliably would require more repetitions, different data volumes, and execution-plan analysis.

The `Stopwatch` measurement covered the EF Core operation and construction of result objects. It **did not** include the complete HTTP response transmission or JSON serialization.

## Query Store: What Does SQL Server See?

This is where the experiment becomes particularly interesting.

The following are the **average engine costs per API request**, calculated from Query Store counter deltas:

| Strategy | SQL CPU / request | Sum of SQL duration / request | Logical reads / request |
|---|---:|---:|---:|
| N+1 | **21.40 ms** | 21.43 ms | **1,103** |
| Include | **1.95 ms** | 1.95 ms | **14** |
| Projection | **2.73 ms** | 2.73 ms | **14** |
| SplitQuery | **1.70 ms** | 1.70 ms | **17** |

For N+1, I measured **1,103 logical reads**, compared with **14** for both Include and Projection—a reduction of approximately **98.7%**.

A previous isolated N+1 run confirmed the same pattern: **1,000 executions** of the OrderItems SELECT and **10 executions** of the Orders SELECT. Together they accounted for **11,030 logical reads** across ten requests, again 1,103 per request.

These are **not physical disk reads**. Logical reads count page accesses within the SQL Server engine, including pages already cached in the buffer pool.

### 101 Cheap Queries Can Cost More Than One Larger Query

A single query fetching one order's items is inexpensive. But N+1 repeats that work, and the application performs many more calls to SQL Server.

The lesson is not that a JOIN is always faster than an indexed lookup. The issue is **the total cost of a business operation**, not the cost of one SQL statement examined in isolation.

For a DBA, that distinction matters. A query with a tiny average duration can still become a serious performance problem when it is executed hundreds of thousands of times.

## The Paradox: Fastest EF Core Time, but Not Lowest SQL CPU

I also compared the three faster strategies:

| Metric | Include | Projection | SplitQuery |
|---|---:|---:|---:|
| Median EF Core time | 6.01 ms | **5.11 ms** | 5.23 ms |
| SQL CPU | 1.95 ms | 2.73 ms | **1.70 ms** |
| Logical reads | **14** | **14** | 17 |
| SQL statements | **1** | **1** | 2 |

**Projection produced the lowest median application time but the highest average SQL CPU among these three variants.** SplitQuery consumed the least average SQL CPU, even though it executed two statements and performed more logical reads.

There is no contradiction. My experiment measured several different parts of the operation:

- SQL Server executes the plan and returns rows;
- EF Core materializes entities or constructs DTOs;
- the application prepares its response objects;
- extra round-trips affect elapsed time, but do not directly equate to SQL CPU.

I am also comparing **a median application elapsed time** with **an average sum of SQL CPU per request**. Subtracting 2.73 ms of SQL CPU from a 5.11 ms application median and calling the difference "EF Core overhead" would be incorrect.

SplitQuery was competitive. That is not a reason to enable `AsSplitQuery()` everywhere: with multiple collections, it can reduce row multiplication caused by JOINs, at the cost of additional SQL statements.

## Reproducing the Experiment

The source code, Docker configuration, SQL scripts, and student instructions are available here:

[**EF Core Performance Lab 67 — Complete Demo**](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab)

Requirements: Docker Desktop, PowerShell 7, and Git. Neither a local .NET SDK nor SSMS is strictly required.

```powershell
git clone https://github.com/marcinpytlik/WWSI_CSharp.git
cd WWSI_CSharp/demonstracje/67_EfCorePerformanceLab

Copy-Item env.template .env
# Set your own strong SQL_SA_PASSWORD in .env.

docker compose up -d --build
Invoke-RestMethod http://localhost:5087/health
```

Once the lab API has initialized the database, configure Query Store for full capture **in the lab database only**:

```sql
ALTER DATABASE EfPerformanceLab
SET QUERY_STORE (
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = ALL
);
```

Verify correctness and run the complete comparison:

```powershell
./scripts/Test-Lab.ps1 -Take 100

./scripts/Run-All-Benchmark.ps1 -Take 100 -Repetitions 10
```

The script runs four isolated series and prints a combined comparison of application elapsed time, SQL CPU, and logical reads. It also saves two token-identified CSV files containing the summary and individual measurements.

**Do not run this experiment against a production database.** The demo deliberately uses a simplified `sa` configuration, deterministic seed data, and automatic schema creation. The repository README explains setup and troubleshooting.

## What About JIT, ReadyToRun, and Native AOT?

Another issue—and a question that came to mind as I analyzed the results—is whether the way I compile the application makes a difference.

If SQL Server consumed approximately 21.40 ms of CPU on average for an N+1 request, while the median EF Core operation took 119.83 ms, **what happens outside the database engine?** How much time is spent in application code, materialization, SQL communication, allocations, and garbage collection?

Could the .NET compilation mode make a difference?

A separate experiment is needed, keeping the data model and SQL workload constant while changing how the application is published:

1. CoreCLR with JIT;
2. ReadyToRun;
3. Composite ReadyToRun;
4. a variant with tiered compilation disabled;
5. Native AOT, provided I can make the application compatible with its restrictions.

Native AOT is not a magic switch that works for every EF Core configuration. A faster application startup also does not automatically imply a lower SQL execution cost.

**I do not yet have JIT-versus-AOT benchmark results for Demo 67.** I do have a reliable baseline for the next experiment.

One thing is already clear: changing how an application is compiled will not, by itself, turn 101 SQL calls into one.

## Conclusions

I take four practical lessons from this lab:

1. **Optimize the complete business operation, not only an individual SELECT.** N+1 can generate thousands of logical reads and many round-trips through apparently cheap statements.
2. **Do not select an approach based only on the EF Core time median.** Also check SQL CPU, execution counts, and logical reads.
3. **Measurement quality matters as much as optimization.** BEFORE/AFTER snapshots and execution-count checks help avoid comparing unrelated historical Query Store data.
4. **There is no universal winner.** Projection, Include, and SplitQuery involve different trade-offs. Choose based on the data model, workload size, and repeatable measurements.

So which strategy won? In my scenario, Projection had the shortest median EF Core time, SplitQuery the lowest average SQL CPU, and N+1 by far the highest overall cost.

But the question that interests me most remains open:

**Will JIT, ReadyToRun, or Native AOT significantly change the elapsed time of the same operation when SQL Server performs exactly the same work?**

That is the subject of the next lab.

---

*All performance results refer to the controlled Demo 67 run `fb6e09ce` on November 22, 2026. I used the same physical workstation for both this and the earlier Startup Lab experiment; the exact SQL Server CU and memory limit of the Demo 67 container were not independently recorded. This is not a universal EF Core or SQL Server benchmark. Source code and methodology: [WWSI_CSharp](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).*
