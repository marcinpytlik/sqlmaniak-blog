---
title: "SQL Server Schema Evolution — A Series of Practical Patterns"
date: 2026-08-05T00:01:00+02:00
slug: "ewolucja-schematu-sql-server-wzorce"
description: "An overview of safe schema evolution patterns: Expand–Contract, Dual Write, Shadow Column, Backfill, compatibility views, Parallel Table, Blue-Green, and Feature Flags."
categories: "Relacyjny Renesans"
tags: [SQL Server,schema evolution,projektowanie baz danych,migracja danych]
draft: false
---

# SQL Server Schema Evolution — A Series of Practical Patterns

A database schema is not a static document. It evolves alongside the application, business processes, reports, and integrations.

The greatest risk usually does not come from the syntax of `ALTER TABLE` itself. It comes from changing a contract used by many independent parts of a system.

This series presents eight patterns for making such changes in a controlled manner.

## 1. Expand–Migrate–Contract

First, add the new structure; next, migrate data and traffic; only then remove the old model.

## 2. Dual Write

Temporarily write to two models. This requires atomicity, idempotency, and a clearly defined source of truth.

## 3. Shadow Column

Create a new column alongside the old one. This allows the type or meaning of data to change safely.

## 4. Backfill in Batches

Migrating data in small batches reduces locking, transaction-log growth, and rollback costs.

## 5. Compatibility View

A view reproduces the old contract for reports and integrations while the physical model has already changed.

## 6. Parallel Table

Build a complete V2 table alongside V1, synchronize the data, validate it, and switch traffic.

## 7. Blue-Green Database Deployment

The blue-green approach requires particular care because a database stores state that keeps changing.

## 8. Feature Flag for Schema Change

Feature flags separate code deployment from activating a new read or write path.

## A Shared Principle

Each pattern addresses a similar set of questions:

- How do we preserve compatibility?
- How do we migrate historical data?
- How do we handle writes during migration?
- How do we verify correctness?
- How do we stop or roll back the change?
- When should temporary solutions be removed?

The goal of this series is not to offer one universal recipe. It is to build a toolkit from which you can select the right technique for the scale and risk of a specific change.

The central idea of the entire series is:

> Safe schema evolution means controlling the transition period between the old and new models.
