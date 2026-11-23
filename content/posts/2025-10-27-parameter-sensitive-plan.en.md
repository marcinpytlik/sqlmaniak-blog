---
title: "Parameter Sensitive Plan: SQL Server's Context-Aware Intelligence"
date: 2025-10-27
slug: parameter-sensitive-plan
tags: [SQLServer, PSP, Performance, QueryOptimization, Internals]
draft: false
---

Every execution plan is a decision about **how to get from data to a result**. For years, SQL Server could cache a plan optimized for an initial parameter value (parameter sniffing) and reuse it even when later values had very different data distributions.

## 💡 What does PSP bring to SQL Server 2022?

**Parameter Sensitive Plan (PSP)** optimization can **maintain multiple plan variants** for **the same query**, tuned for different parameter selectivities. A **dispatcher** chooses the appropriate variant for the current parameter values.

- One logical query can have multiple plan variants.
- Query Store captures information that helps analyze them.
- At runtime, selection depends on parameter selectivity ranges, or “buckets”.

📂 Repository: [PSP](https://github.com/marcinpytlik/SQLManiak/tree/master/sqlmaniak_blog/PSP-DEMO)

## ⚙️ Running the demo

1. Open the repository in VS Code.
2. Set the environment variables:

   ```powershell
   $env:MSSQL_SERVER="localhost"
   $env:MSSQL_USER="sa"
   $env:MSSQL_PASS="YourStrong!Passw0rd"
   ```

3. Run tasks **00 → 03**, followed by **04 – Compare IO/CPU**, or execute the queries in `sql/dmv`.

## 🔬 What you will see

- **At least two plan variants** in Query Store for `dbo.GetOrdersByCustomer`.
- In the plan XML: `<ParameterSensitivePlan>True</ParameterSensitivePlan>`.
- I/O and CPU differences between infrequent and “hot” parameter values.

## 🧩 Good practices

- Keep **Query Store in READ_WRITE** mode to analyze PSP behavior.
- Be careful when combining PSP with `OPTIMIZE FOR` hints.
- PSP targets eligible parameterized statements, including stored procedures and `sp_executesql`.

> “Intelligence is the ability to adapt to change.” — *Stephen Hawking*
