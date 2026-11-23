---
title: "PIOSEE: an incident-response framework for DBAs with a reusable template"
date: "2025-10-04"
slug: "piosee-framework-dla-dba-en"
draft: false
description: "A practical Problem–Information–Options–Select–Execute–Evaluate template for SQL Server incidents."
tags: ["DBA","Incidents","Runbook"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/piosee-framework-dla-dba.png"

---

## Introduction
When production is on fire, you need a procedure, not poetry. PIOSEE is a six-step framework for staying calm and protecting data.

## Template
**P – Problem:** Describe the symptom and a metric (for example `Backup FULL > 4h`).
**I – Information:** Record facts, DMVs and logs without interpreting them.
**O – Options:** List possible solutions without evaluating them yet.
**S – Select:** Choose based on time, risk and impact.
**E – Execute:** Define the execution plan and communication.
**E – Evaluate:** Assess outcomes, lessons learned and monitoring.

## Example: transaction log 95% full
- **Problem:** `% Log Used` reaches 95% in MyDb.
- **Information:** No `BACKUP LOG` for 18 hours; `vlf_active=1` at the end of the file.
- **Options:** Back up the log, temporarily enlarge it, or terminate a long transaction.
- **Select:** Back up the log and expand it to 64 GB; do not kill the transaction.
- **Execute:** Run `BACKUP LOG` and `ALTER DATABASE ... MODIFY FILE`; notify the team.
- **Evaluate:** VLF count is acceptable, `% Used < 30%`, alert created.

## Ready-to-copy Markdown
```
# PIOSEE – Incydent: <tytuł>

## P – Problem
<co nie działa>

## I – Information
<logi/DMV/screeny>

## O – Options
- [ ] Opcja A
- [ ] Opcja B

## S – Select
Wybrano: <opcja>, uzasadnienie.

## E – Execute
Kroki, właściciele, okno, rollback plan.

## E – Evaluate
Wynik, metryki po, wnioski, zadania follow‑up.
```
