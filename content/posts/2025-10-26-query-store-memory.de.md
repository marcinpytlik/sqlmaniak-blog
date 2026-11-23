---
title: "Query Store: Gedächtnis der Pläne, Gedächtnis der Fehler"
date: 2025-10-26
slug: query-store-memory
tags: [SQLServer, QueryStore, Performance, Internals, Plans]
draft: false
---

Query Store ist das Langzeitgedächtnis von SQL Server: Es speichert Pläne, Entscheidungen und manchmal auch Fehler. Mit der Ausführungshistorie können DBAs die Entwicklung der Performance verfolgen und aus Regressionen lernen. Wie ein Tagebuch vergangener Tage — manchmal voller Erkenntnisse, manchmal voller Reue.

## 🧠 Wie Query Store funktioniert

Von SQL Server verarbeitete Abfragen können im **Query Store** erfasst werden, zusammen mit Ausführungsplänen und Laufzeitstatistiken. Im Laufe der Zeit sammelt die Engine Hinweise darauf, welche Pläne gut liefen und welche Regressionen verursachten.

> Query Store könnte man als „Blackbox“ von SQL Server bezeichnen: Es dokumentiert Optimizer-Entscheidungen über längere Zeit.

## ⚙️ Query Store aktivieren

```sql
ALTER DATABASE [AdventureWorks2022]
SET QUERY_STORE = ON
(
    OPERATION_MODE = READ_WRITE,
    CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30),
    DATA_FLUSH_INTERVAL_SECONDS = 900,
    INTERVAL_LENGTH_MINUTES = 60,
    MAX_STORAGE_SIZE_MB = 1024
);
```

## 🔍 Ein Blick in die Views

```sql
SELECT TOP 20 
    qs.query_id, p.plan_id, rs.avg_duration, rs.last_execution_time
FROM sys.query_store_query AS qs
JOIN sys.query_store_plan AS p ON qs.query_id = p.query_id
JOIN sys.query_store_runtime_stats AS rs ON p.plan_id = rs.plan_id
ORDER BY rs.last_execution_time DESC;
```

## 🧩 Planregression

```sql
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 7;
```

## 🧹 Query Store leeren

```sql
ALTER DATABASE [AdventureWorks2022] SET QUERY_STORE CLEAR ALL;
```

> Ein DBA, der die Historie löscht, verliert die Möglichkeit, daraus zu lernen.

## 💬 Gedanken dazu

Query Store ist mehr als eine technische Funktion. Es ist eine Metapher für das Lernen aus Fehlern — sowohl für SQL Server als auch für uns Administratoren.

> „Wer sich nicht an die Vergangenheit erinnern kann, ist dazu verurteilt, sie zu wiederholen.“ — *George Santayana*

## ✅ Checkliste

[DBA-Checkliste ansehen](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/QueryStore/checklists/QueryStore-Checklist.md)

📂 Repository: [SQLManiak/QueryStore-Labs](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/QueryStore)
