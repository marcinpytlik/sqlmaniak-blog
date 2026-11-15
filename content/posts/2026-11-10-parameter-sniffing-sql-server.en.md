---
title: "Parameter Sniffing — When the Same Plan Works for One Parameter but Not Another"
date: 2026-11-10T08:00:00+01:00
slug: parameter-sniffing-sql-server
description: "A practical introduction to parameter sniffing in SQL Server: how to identify and measure the problem and when to consider PSP, RECOMPILE, or other approaches."
tags: [SQLServer, ParameterSniffing, Performance, QueryTuning, DBA]
categories: [SQL Server]
draft: false
---

Parameter sniffing is not inherently a bug.

When compiling a stored procedure, SQL Server can use parameter values to choose an execution plan. Problems arise when the data distribution is skewed.

## Example

```sql
CREATE OR ALTER PROCEDURE dbo.GetOrdersByCustomer
    @CustomerId int
AS
BEGIN
    SELECT
        OrderId,
        CustomerId,
        OrderDate,
        TotalAmount
    FROM dbo.Orders
    WHERE CustomerId = @CustomerId;
END;
GO
```

If one customer has 5 orders and another has 5 million, a single plan may not suit both.

## Common symptoms

- The procedure is fast on one execution and very slow on another.
- Restarting or recompiling helps, but only temporarily.
- The plan changes after a deployment or failover.
- Execution time depends on the parameter value used for the first compilation.
- Query Store shows considerable variation.

## RECOMPILE

```sql
OPTION (RECOMPILE);
```

A new plan is generated, at the cost of recompilation.

## OPTIMIZE FOR

```sql
OPTION (OPTIMIZE FOR UNKNOWN);
```

This is not a universal solution. It must fit the actual data distribution.

## Parameter Sensitive Plan

In SQL Server 2022, with an appropriate database compatibility level, the engine may use Parameter Sensitive Plan (PSP) optimization to maintain multiple plan variants for different parameter-value ranges.

## Takeaway

If a procedure sometimes performs well and sometimes badly, do not start by restarting the server.

Inspect the parameter values, data distribution, and plan history.
