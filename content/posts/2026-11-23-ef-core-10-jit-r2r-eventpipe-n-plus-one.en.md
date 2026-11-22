---
title: "EF Core Through a DBA's Eyes: Can JIT Rescue N+1? .NET 10, ReadyToRun, and EventPipe"
date: 2026-11-23T08:00:00+01:00
slug: "ef-core-10-jit-readytorun-eventpipe-n-plus-one"
description: "A follow-up to the EF Core 10 and SQL Server 2022 lab: 640 measurements while profiling JIT, ReadyToRun, Composite, and No-tiering, with counters, traces, GC, and allocations."
category: "Relational Renaissance"
tags:
  - SQL Server
  - EF Core
  - .NET 10
  - Query Store
  - JIT
  - ReadyToRun
  - EventPipe
  - performance tuning
  - ORM
draft: true
---

# EF Core Through a DBA's Eyes: Can JIT Rescue N+1? .NET 10, ReadyToRun, and EventPipe

**If the same EF Core operation executes 101 SQL commands instead of one, can faster .NET compilation make up for the difference?**

That question stayed with me after [my previous article on N+1, Include, Projection, SplitQuery, and Query Store](/posts/ef-core-n-plus-one-include-projection-split-query-query-store/). With identical data—**100 orders and 1,000 order items**—I measured medians of **119.83 ms for N+1** and **5.11 ms for Projection**. On the SQL Server side, the difference was **1,103 versus 14 logical reads** per request.

This time, I am going further without changing the queries or the database schema. Instead, I change **how the .NET 10 application is published**, observe the process with `dotnet-counters` and `dotnet-trace`, and compare the results with my earlier Query Store observations.

I am not trying to declare a winner at any cost. I want to establish **what CLR counters can actually tell us when SQL Server performs the same work**.

**Code, scripts, and documentation: [WWSI_CSharp — Demo 67, EF Core Performance Lab](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).** More detailed tables and methodological caveats are available in the [final report for Experiment 03](https://github.com/marcinpytlik/WWSI_CSharp/blob/main/demonstracje/67_EfCorePerformanceLab/experiments/03_Compilation/FINAL-REPORT-2026-11-22.md).

## First, a reminder: what stays constant?

The application uses **ASP.NET Core / .NET 10, EF Core 10, and SQL Server 2022 Developer** in Linux containers. The `EfPerformanceLab` database holds 100 orders, each containing 10 items.

All four endpoints return identical DTOs, and an automated test checks result equality. Every implementation uses `AsNoTracking()`.

| Strategy | Data retrieval | SQL commands per request |
|---|---|---:|
| N+1 | Read orders, then issue a separate SELECT for each order's items | **101** |
| Include | `Include()` and `AsSingleQuery()` | **1** |
| Projection | `Select()` directly into DTOs | **1** |
| SplitQuery | `Include()` and `AsSplitQuery()` | **2** |

N+1 is **a deliberately implemented anti-pattern**, not an accidental consequence of lazy loading. That lets me reproduce the problem rather than depend on a particular navigation-property configuration.

From a DBA's perspective, what matters is the number of operations produced by **one business request**, not merely the cost of a single SELECT.

## Four ways of running the same application

In a separate publishing experiment, I prepared four variants. All use **Release, linux-x64, and self-contained deployment**. Self-contained publishing is particularly important for Composite ReadyToRun.

| Mode | Publishing/runtime configuration | Tiered Compilation |
|---|---|---|
| `jit` | `PublishReadyToRun=false` | Enabled |
| `r2r` | `PublishReadyToRun=true` | Enabled |
| `composite` | `PublishReadyToRunComposite=true` | Enabled |
| `no-tiering` | Published like `jit`, `TieredCompilation=0` | Disabled |

`no-tiering` is not another compilation technology. It changes runtime behavior: I disable tiered compilation, potentially changing the trade-off between compilation overhead and the quality of generated code.

An earlier phase, **03B**, was designed to help separate these effects: four balanced rounds with varying mode order, using 10 repetitions of each strategy. That is **4 rounds × 4 modes × 4 strategies × 10 repetitions = 640 application samples**. The next phase, **03C**, sampled process-wide metrics (CPU, allocations, GC collections). This article focuses mainly on **03D**, a separate experiment using EventPipe tools.

This distinction matters: **the 640 samples from 03B and the 640 from 03D are different datasets**, collected under different conditions.

## How did I attach EventPipe to a process in Docker?

The application runs in a runtime image, while the diagnostic tools run in **a separate `profiler` container** based on .NET SDK 10.

In Docker Compose, the profiler shares two resources with the API:

- the PID namespace (`pid: "service:api"`);
- the `/tmp` volume, where .NET exposes its diagnostic socket.

This allows `dotnet-counters ps` to discover the application process, and the tools can attach without installing an SDK in the API's runtime image.

Example collection commands inside the profiler container:

~~~bash
/tools/dotnet-counters collect \
    --process-id 1 \
    --refresh-interval 1 \
    --format csv \
    --counters System.Runtime \
    --output /output/jit-counters.csv
~~~

~~~bash
/tools/dotnet-trace collect \
    --process-id 1 \
    --profile dotnet-common,dotnet-sampled-thread-time \
    --output /output/jit-trace.nettrace
~~~

**I do not run both profilers at the same time.** Each tool gets its own request workload. The traces cover the process **after it has started and warmed up**; they do not measure CLR cold startup or the complete initial JIT cost.

In phase 03D, for each mode I ran **20 repetitions of all four strategies** while collecting `dotnet-counters` data, followed by another 20 repetitions while collecting `dotnet-trace` data:

**4 modes × 4 strategies × 20 repetitions × 2 collection types = 640 measured EF Core operations.**

Before each measurement session, an automated test verified the returned data and the SQL command counts: **101 / 1 / 1 / 2**.

## Timing under profiling: N+1 still stands out

These tables show the **median duration of the EF Core operation itself**, not full HTTP latency or SQL Server CPU time.

### `dotnet-counters` session — median in ms

| Strategy | JIT | R2R | Composite R2R | No-tiering |
|---|---:|---:|---:|---:|
| **N+1** | **135.13** | **177.27** | **136.99** | **169.22** |
| Include | 6.27 | 7.39 | 6.64 | 9.79 |
| Projection | **5.76** | 6.75 | 6.09 | 6.20 |
| SplitQuery | 6.46 | 6.67 | 6.55 | 7.71 |

### `dotnet-trace` session — median in ms

| Strategy | JIT | R2R | Composite R2R | No-tiering |
|---|---:|---:|---:|---:|
| **N+1** | **137.43** | **145.46** | **142.01** | **178.11** |
| Include | 8.00 | 7.35 | 8.51 | 11.06 |
| Projection | **6.05** | 6.66 | 6.89 | 7.48 |
| SplitQuery | 6.67 | **6.17** | 6.52 | 7.66 |

The most striking observation is not about R2R. **Across all measured modes, N+1 remains more than an order of magnitude slower than the other strategies.** In the JIT session with `dotnet-counters`, the ratio between N+1 and Projection medians was approximately **23.5:1**.

That does not mean JIT is inherently better than ReadyToRun. These are **local medians from profiling sessions executed in a fixed order**. Profiling adds overhead, and this phase was not counterbalanced.

To discuss the repeatability of compilation-mode effects, I must return to the separate, balanced **03B** rounds rather than select the smallest number from the 03D tables.

## What do System.Runtime counters show?

Beyond the operation medians, I examined metrics for **the entire API process**. Here is the `dotnet-counters` summary:

| Metric | JIT | R2R | Composite | No-tiering |
|---|---:|---:|---:|---:|
| Process allocations, MB* | 124.4 | 123.0 | 124.0 | 125.3 |
| JIT time, s* | 3.04 | 2.92 | 2.86 | 0.04 |
| Methods JIT-compiled* | 3,752 | 3,278 | 2,808 | 63 |
| User CPU time, s* | 4.84 | 5.16 | 4.86 | 3.05 |
| Median working set, MB | 185.4 | 188.7 | 199.3 | 164.3 |
| Gen0 collections* | 7 | 7 | 8 | 8 |

\* Values aggregated from time-series counter samples (`System.Runtime`, approximately one-second intervals) are **estimates** whose interpretation depends on each counter's semantics. They do not measure a single EF Core invocation.

The `no-tiering` variant reported substantially less JIT compilation activity during collection, yet its median operation times were generally higher than those of the other modes.

That is a useful warning against simplistic reasoning:

> Less time spent in JIT compilation does not necessarily mean lower operation latency in an already running application.

However, **this does not prove causation**. Generated code quality, process state, warm-up, test order, and profiling overhead may all play a role. This table alone cannot justify a universal recommendation to enable or disable tiering.

### What about GC and memory?

Across these sessions, approximate total process allocations were close—around **123–125 MB**. There is no order-of-magnitude change here that would, by itself, explain the performance gap between N+1 and Projection.

**Working set is not an allocation metric**, and the number of Gen0 collections does not directly express the GC cost attributable to an individual endpoint. We are measuring the ASP.NET Core server, including HTTP processing, serialization, libraries, and runtime activity.

To demonstrate that a specific period was spent in GC or JIT, I would need to examine events and stacks within the relevant time window, not only aggregate counters.

## An experimental trap: a valid trace file is not necessarily a complete trace

While automating the diagnostics, I encountered a problem worth discussing on its own.

For the original `3b971dd5` series, I used a limit of:

~~~text
dotnet-trace --duration 150s
~~~

But the complete request workload took approximately **168–170 seconds**. The tool correctly saved a `.nettrace` file, yet stopped collecting data **before the workload had finished**.

What does that imply?

I cannot map the full history of 80 requests to a trace that covers only part of it. Nor can I claim that the larger Composite R2R trace—approximately **157 MB** in the historical run—proves higher CPU, memory consumption, or GC overhead. Trace size also depends on the number and kinds of events recorded.

I fixed the automation so that `dotnet-trace` continues until the request workload ends, then receives **Enter through a pseudo-terminal and FIFO**. Similarly, `dotnet-counters` receives `q` to stop gracefully. The solution also required enforcing **LF line endings** for the Bash script built from the repository on Windows.

**The new mechanism passed an integration test on Docker Desktop (run `b8e2a335`):**

- `PASS jit counters` — a **266,456-byte** CSV was saved;
- `PASS jit trace` — a **26,108,814-byte** `.nettrace` file was saved;
- all four strategies passed the result-equality checks.

This test **confirms that the new session ended and was saved correctly after the workload**. I am not presenting it as an independent examination of every event's timeline within the file.

## Why can't we subtract SQL time from EF Core time?

Let me return to the original Query Store results:

| Strategy | Median EF operation, ms | Average SQL CPU per request, ms | Logical reads per request |
|---|---:|---:|---:|
| N+1 | 119.83 | 21.40 | 1,103 |
| Include | 6.01 | 1.95 | 14 |
| Projection | **5.11** | 2.73 | **14** |
| SplitQuery | 5.23 | **1.70** | 17 |

It may be tempting to subtract 21.40 ms from the 119.83 ms median and call the remainder “EF Core overhead.” That would be a methodological mistake.

First, an operation's **median duration** and **average SQL CPU** are not comparable statistical quantities. Second, SQL Server CPU time is not the time the client spends waiting for a result. Third, the application also performs materialization, waits, round trips, scheduling, and DTO construction.

That is why I needed **three perspectives**:

1. `Stopwatch` inside the API — how long the operation takes;
2. **Query Store** — what work the SQL Server statements perform;
3. **EventPipe and CLR counters** — what the overall application process does during the workload.

No single one explains the complete system.

## How can you reproduce the profiling experiment?

The lab is available in the [WWSI_CSharp repository, Demo 67](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).

After configuring `.env` and starting the lab SQL Server, open the Demo 67 directory:

~~~powershell
git clone https://github.com/marcinpytlik/WWSI_CSharp.git
cd WWSI_CSharp/demonstracje/67_EfCorePerformanceLab

Copy-Item env.template .env
# Set your own strong SQL_SA_PASSWORD in .env.

docker compose up -d sql

./experiments/03_Compilation/Run-EventPipeDiagnostics.ps1 `
    -Modes jit `
    -Take 100 `
    -Repetitions 10 `
    -CaptureSeconds 300
~~~

To test all compilation modes:

~~~powershell
./experiments/03_Compilation/Run-EventPipeDiagnostics.ps1 `
    -Modes jit,r2r,composite,no-tiering `
    -Take 100 `
    -Repetitions 20 `
    -CaptureSeconds 300
~~~

The results are written to `experiments/03_Compilation/results/`: counter CSVs, per-request CSVs, `.nettrace` files, logs, and manifests.

`CaptureSeconds` is now **advisory**. If the workload exceeds it, the script reports a warning but does not interrupt data collection before all requests finish.

**Do not use this setup against a production SQL Server.** The demo uses local containers, synthetic data, a simplified `sa` account, and a shared diagnostics namespace.

## Conclusions: queries first, compiler second

Five findings stand out.

**First:** N+1 remains the dominant issue in every runtime configuration tested. The compiler cannot turn 101 SQL commands into one.

**Second:** For this data volume, Projection, Include, and SplitQuery deliver operation times of roughly the same order of magnitude, but differ in SQL shape, round trips, and database-engine cost.

**Third:** less JIT activity does not guarantee lower latency. Compilation cost and the execution performance of compiled code are distinct concerns.

**Fourth:** process counters and Query Store measure different domains. I do not attribute all API allocations to an individual EF Core operation, or SQL CPU time to HTTP response latency.

**Fifth:** the fact that a profiler saved a file is not enough. You also need to verify that it covers **the entire interval under investigation**.

In the previous article, I asked whether compilation strategy could meaningfully affect the duration of the same operation. After further measurements, my answer is: **there may be an effect, but in this lab its scale did not approach the consequences of choosing N+1**. I also have no basis for declaring any compilation mode universally the fastest.

**When tuning EF Core, a DBA's first question should not be “how does JIT work?” but “how many SQL queries does this operation actually generate, and what does Query Store show?”**

---

*03D run: `3b971dd5`, November 22, 2026, 640 profiled operation measurements. The EventPipe termination fix was validated separately in run `b8e2a335`. Earlier Query Store data: 10 repetitions per strategy, run `fb6e09ce`. These results come from a local lab and are not a universal benchmark of EF Core, SQL Server, or .NET compilation modes. Raw traces were not analyzed for event stacks or timelines. Source code and full report: [Demo 67](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).*
