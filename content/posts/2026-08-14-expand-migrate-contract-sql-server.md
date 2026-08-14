---
title: "Expand–Migrate–Contract: SQL-Server-Schema sicher ohne Big-Bang-Migration verändern"
date: 2026-08-14T08:01:00+02:00
slug: "expand-migrate-contract-sql-server"
description: "Expand–Migrate–Contract ist ein Muster für sichere Schema-Evolution in SQL Server. Neue Strukturen werden zuerst hinzugefügt, Daten und Anwendungen schrittweise migriert und alte Strukturen erst nach erfolgreicher Validierung entfernt."
categories:
  - "Relationale Renaissance"
tags:
  - "SQL Server"
  - "SQL Server auf Deutsch"
  - "Schema Evolution"
  - "Expand Migrate Contract"
  - "Datenbankdesign"
  - "Datenmigration"
  - "Relationale Renaissance"
draft: false
---

Eine Schemaänderung sieht auf einem Whiteboard oft sehr einfach aus.

Eine Spalte wird nicht mehr benötigt.

Eine neue Tabelle soll entstehen.

Ein Attribut bekommt eine neue Struktur.

Technisch könnte die Lösung manchmal aus wenigen SQL-Anweisungen bestehen.

```sql
ALTER TABLE ...