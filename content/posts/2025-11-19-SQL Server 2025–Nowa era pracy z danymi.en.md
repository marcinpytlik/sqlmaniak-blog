---
title: "SQL Server 2025 — A New Era of Working with Data"
date: 2025-11-19
tags: [SQL Server, SQL Server 2025, Performance, Monitoring, Security, Query Store, JSON]
categories: [SQLManiak]
draft: false
---

SQL Server 2025 (17.x) introduces meaningful changes for DBAs, architects, and developers, particularly in query processing, new data types, AI integration, and workload management. However, it is important to distinguish generally available functionality from features requiring **PREVIEW_FEATURES**.

This overview is based on official Microsoft documentation rather than unverified feature names.

## Intelligent Query Processing and Query Store

SQL Server 2025 extends the **Intelligent Query Processing (IQP)** family with:

- **Optional Parameter Plan Optimization (OPPO)** — uses Multiplan infrastructure to provide plan variants for queries with optional predicates.
- **Cardinality Estimation Feedback for Expressions** — learns which estimation models work for expressions.
- **Degree of Parallelism (DOP) Feedback** — enabled by default.
- **Query Store for readable secondaries** — enabled by default in supported configurations.
- **ABORT_QUERY_EXECUTION** — a hint that can block subsequent executions of known problematic queries.

There is no separately documented product named “Query Store 3.0.” Performance diagnostics still require execution plans, wait statistics, Query Store, and application measurements.

## Native JSON Data Type

SQL Server 2025 provides the native **`json`** type, which stores JSON in an optimized binary representation.

Do not call it **`JSONB`**: that name is primarily associated with PostgreSQL, not the SQL Server data type.

Additional JSON features include **`JSON_OBJECTAGG`** and **`JSON_ARRAYAGG`**. Before migration, verify limitations, driver compatibility, indexing behavior, and actual query performance.

## VECTOR Data Type and AI

The new **`vector`** type stores vector representations used for similarity search and related workloads.

Functions include **`VECTOR_DISTANCE`**, **`VECTOR_NORM`**, and **`VECTOR_NORMALIZE`**, alongside integrations with external AI models.

**Important:** approximate vector indexes and certain vector-search capabilities are Preview features and require the appropriate **`PREVIEW_FEATURES`** configuration. Do not assume Preview features are production-ready.

## Regular Expressions and T-SQL

T-SQL now supports regular-expression functionality including:

- **`REGEXP_LIKE`** — test whether a pattern matches;
- **`REGEXP_REPLACE`** — replace matching text;
- **`REGEXP_SUBSTR`** — extract matching substrings;
- **`REGEXP_COUNT`** — count matches.

These additions simplify some validation and transformation tasks, but their performance should be measured under real workloads.

## Optimized Locking and TempDB

**Optimized Locking** reduces lock memory consumption and can reduce blocking and lock escalation. Check edition, prerequisites, and database configuration.

SQL Server 2025 also introduces **TempDB Space Resource Governance**, helping protect TempDB from runaway space consumption, and **Accelerated Database Recovery in TempDB**.

These improvements do not eliminate every `PAGELATCH` wait or guarantee a particular percentage of performance improvement.

## Columnstore, Analytics, and Integrations

Documented columnstore enhancements include **ordered nonclustered columnstore indexes** and improvements to index builds.

SQL Server 2025 also extends integrations with Microsoft Fabric and data tooling. Availability depends on edition, configuration, and feature release status.

## Security and Deployment

When planning a migration, review documented security, connectivity, permission, and application-compatibility changes for the target build.

Do not assume there are official modules called “Security Shield” or “Secure Credential Vault” without product documentation.

Similarly, do not assume that official native ARM64 SQL Server container images or clusterless Availability Groups are supported merely because of broad platform announcements.

## DBA Predeployment Checklist

1. **Application and driver compatibility**, including new data types.
2. **Query Store and plan regressions**, comparing baseline metrics before and after upgrade.
3. **Preview features**, including whether they are enabled and appropriate for the environment.
4. **Edition-specific availability** across Enterprise, Standard, and Express.
5. **Backup/restore, HA/DR, and performance tests** — a new engine version does not replace operational validation.

## Summary

SQL Server 2025 brings real improvements: native `json`, `vector`, regex functions, IQP enhancements, Optimized Locking, and TempDB resource controls.

The most important DBA principle remains unchanged: **verify the feature in official documentation, then test it against your workload**.

Sources:

- [What's New in SQL Server 2025 — Microsoft Learn](https://learn.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-2025?view=sql-server-ver17)
- [SQL Server 2025 Release Notes](https://learn.microsoft.com/en-us/sql/sql-server/sql-server-2025-release-notes?view=sql-server-ver17)
- [Editions and Supported Features](https://learn.microsoft.com/en-us/sql/sql-server/editions-and-components-of-sql-server-2025?view=sql-server-ver17)
