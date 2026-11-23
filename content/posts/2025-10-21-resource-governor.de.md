---
title: "Resource Governor: CPU begrenzen, nicht Menschen"
date: 2025-10-21
slug: resource-governor
tags: [SQLServer, Performance, ResourceGovernor, TSQL, DBA]
draft: false
---

# Resource Governor: CPU begrenzen, nicht Menschen

Nicht jeder Prozess verdient 100 % CPU. Nicht jeder Benutzer sollte eine freie Autobahn zu allen Kernen haben. Resource Governor bewahrt das Gleichgewicht, indem er Grenzen setzt, bevor Chaos entsteht.

SQL Server kann beinahe zu entgegenkommend sein. Wenn eine Clientanwendung Berichte mit spaghettiartigen JOINs verarbeitet, stellt der Server ihr möglicherweise viele Ressourcen zur Verfügung, während andere Benutzer im Stau stehen. Resource Governor sagt: *Genug*.

Das ist keine Strafe, sondern **eine faire Verteilung von Rechenressourcen**.

Mit Resource Governor kannst du Ressourcen (CPU, Arbeitsspeicher und I/O) auf **Workload Groups** verteilen und Sitzungen nach eigenen Regeln zuweisen. Stell dir ein Großraumbüro vor: Jede Anwendung bekommt ihren Tisch, ihren Stuhl und eine Kaffeezuteilung.

---

## ⚙️ So funktioniert es

1. **Resource Pools** definieren minimale und maximale Anteile an CPU und Arbeitsspeicher. Beispielsweise wird `PoolReporty` mit maximal 30 % CPU und 20 % Arbeitsspeicher konfiguriert.
2. **Workload Groups** ordnen Sitzungen bestimmten Pools zu. Reporting, OLTP und Tests haben jeweils ihren Platz.
3. **Classifier Function** ist das Herzstück: Eine T-SQL-Funktion erkennt eingehende Verbindungen und entscheidet, welcher Gruppe sie zugeordnet werden.

---

## 🧠 Konfigurationsbeispiel

```sql
-- 1. Włącz Resource Governor
ALTER RESOURCE GOVERNOR RECONFIGURE;

-- 2. Utwórz Resource Pool
CREATE RESOURCE POOL PoolReporty
WITH (MAX_CPU_PERCENT = 30, MAX_MEMORY_PERCENT = 20);

-- 3. Utwórz Workload Group
CREATE WORKLOAD GROUP GrupaReporty
USING PoolReporty;

-- 4. Funkcja klasyfikująca
CREATE FUNCTION dbo.fnClassifier()
RETURNS sysname
WITH SCHEMABINDING
AS
BEGIN
    DECLARE @Group sysname;
    IF ORIGINAL_LOGIN() LIKE 'report%'
        SET @Group = 'GrupaReporty';
    ELSE
        SET @Group = 'default';
    RETURN @Group;
END;
GO

-- 5. Przypisz funkcję
ALTER RESOURCE GOVERNOR
WITH (CLASSIFIER_FUNCTION = dbo.fnClassifier);

ALTER RESOURCE GOVERNOR RECONFIGURE;
```

Jetzt erhalten Reporting-Benutzer ihren CPU-Anteil, während der restliche Server wieder Luft bekommt.

---

## 🔬 Überprüfung

Sieh dir die DMVs an:

```sql
SELECT pool_id, name, min_cpu_percent, max_cpu_percent
FROM sys.resource_governor_resource_pools;

SELECT group_id, name, pool_id
FROM sys.resource_governor_workload_groups;
```

Auch über `sys.dm_resource_governor_workload_groups` kannst du Ausführungsstatistiken einsehen und besonders ressourcenintensive Workloads erkennen.

---

## 🧩 Ein Gedanke von SQLManiak

In der Welt der Prozesse möchte jeder König der CPU sein. Doch echtes Gleichgewicht entsteht nicht durch rohe Gewalt, sondern durch **bewusste Verteilung**.

Resource Governor ist ein Werkzeug für philosophische DBAs: Er zeigt, dass Grenzen eine Voraussetzung für Harmonie sein können.

> „Nicht jede Anwendung ist gleich — aber jede verdient ihre eigenen 30 % CPU.“
