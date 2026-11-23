---
title: "FCI vs Always On AG: choosing an architecture and defining RTO/RPO"
date: "2025-10-04"
slug: "fci-vs-ag-rto-rpo-en"
draft: false
description: "A practical comparison of FCI and AG, with decision scenarios and measurable recovery objectives."
tags: ["SQL Server","FCI","AlwaysOn AG"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/fci-vs-ag-rto-rpo.png"

---

## Introduction
FCI and AG are not inherently “better” or “worse”; each fits different requirements. Let's make the choice systematically.

## In one sentence
- **FCI:** *instance-level* high availability with shared storage; no read scaling.
- **AG:** *database-level* availability with readable replicas and independent storage.

## When to choose FCI
- You already have a SAN and want minimal application changes.
- You are migrating legacy instances with dependencies on `msdb` or `master`.
- Example targets: RTO around 1–2 minutes and RPO around zero with shared storage; verify these through testing.

## When to choose AG
- You need read workloads on secondary replicas.
- Each node has independent storage.
- You need disaster recovery at another site, with synchronous or asynchronous modes.

## Measure, don't guess
- Measure instance restart time, recovery time of the largest database and inter-node network behavior.
- RTO = failure detection + failover + recovery.
- For asynchronous AG, RPO depends on the amount of data not yet hardened at the secondary, not simply redo delay.

## Decision checklist
- [ ] Application requirements (connection strings, listener?)
- [ ] Budget and storage (SAN versus local NVMe)
- [ ] Read-only workloads?
- [ ] Enterprise licensing requirements?
- [ ] Operational team: who can support AG complexity?

> Test failover quarterly. Untested HA is only a promise.
