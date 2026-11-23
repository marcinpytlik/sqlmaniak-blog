---
title: "SQL Server Memory Internals: Was geschieht im Buffer Pool?"
date: 2025-10-22
slug: memory-internals
tags: [SQLServer, Internals, Memory, Performance, DBA]
draft: false
---

Hinter jeder Operation steht Arbeitsspeicher: **Buffer Pool**, **Memory Clerks**, **Lazy Writer** und **PLE (Page Life Expectancy)**. Sie bilden das Herz von SQL Server; ein starker PLE-Rückgang kann ein Warnsignal sein. Wer versteht, wie SQL Server Datenseiten verwaltet, kann gezielt optimieren.

> „Was nicht in den Arbeitsspeicher passt, kehrt von der Festplatte zurück und rächt sich.“

---

## 🧠 Speicherarchitektur von SQL Server

SQL Server besitzt eigene Speicherverwaltungsmechanismen, die mit dem Betriebssystem zusammenarbeiten. So kann die Engine auf Last reagieren und interne Zuweisungen steuern.

Die wichtigsten Komponenten:

| Bereich | Beschreibung |
|---|---|
| **Buffer Pool** | Puffert 8-KB-Datenseiten und unterstützt Lese- und Schreibzugriffe. |
| **Plan Cache** | Speichert kompilierte Abfragepläne; ein übergroßer Cache kann mit anderen Speicherverbrauchern konkurrieren. |
| **Memory Clerks** | Erfassen Speicherzuweisungen für die Subsysteme von SQL Server. |
| **Workspace Memory** | Speicher für Sortierungen, Hash Joins und Aggregationen. |
| **Stolen Memory** | Vom Buffer-Pool-Manager verwalteter Speicher für Aufgaben außerhalb des Datenseiten-Caches. |

---

## 🔄 Wie SQL Server Seiten verwaltet

Eine Datenseite kann mehrere Phasen durchlaufen:

1. **Physical Read** — die Seite wird vom Datenträger in den Buffer Pool gelesen.
2. **Use in Query** — eine Abfrage greift auf die gepufferte Seite zu.
3. **Dirty Page** — die Seite wurde geändert, aber noch nicht auf den Datenträger geschrieben.
4. **Checkpoint / Lazy Writer** — Hintergrundmechanismen schreiben geänderte Seiten bei Bedarf.
5. **Eviction (LRU)** — Seiten können bei Speicherbedarf aus dem Cache entfernt werden.

SQL Server nutzt eine **LRU-ähnliche Strategie (Least Recently Used)** und weitere Mechanismen, um über die Verdrängung von Seiten zu entscheiden.

---

## 📊 Wichtige Kennzahlen

| Kennzahl | Bedeutung |
|---|---|
| **Page Life Expectancy (PLE)** | Ungefähre Verweildauer einer Seite im Cache. Anhaltende Rückgänge können auf Speicherdruck hindeuten. |
| **Lazy Writes/sec** | Anzahl der vom Lazy Writer pro Sekunde geschriebenen Seiten. |
| **Memory Grants Pending** | Abfragen, die auf eine Arbeitsspeicherzuteilung warten. |
| **Target vs Total Server Memory** | Vergleich zwischen aktuellem Speicherverbrauch und Zielwert von SQL Server. |
| **Memory Clerks** | Welche Subsysteme Speicher verbrauchen, etwa Buffer Pool, Abfrageausführung oder Lock Manager. |

---

## 🧩 Diagnose Schritt für Schritt

📁 Im Repository findest du einsatzbereite Skripte:

| Skript | Beschreibung |
|---|---|
| `Target_vs_Total_Server_Memory.sql` | Zielwert und aktuellen Speicherverbrauch vergleichen. |
| `BufferPool_PLE_Counters.sql` | PLE-Trends pro NUMA-Knoten. |
| `Memory_Clerks_Overview.sql` | Größte Speicherverbraucher ermitteln. |
| `Memory_Grants_Status.sql` | Abfragen finden, die auf Memory Grants warten. |
| `LazyWriter_Checkpoint_Stats.sql` | Hintergrund-Schreibaktivität untersuchen. |
| `BufferPool_ModifiedPages.sql` | Dirty Pages pro Datenbank. |
| `Waits_Memory_Pressure.sql` | Wartezeiten im Zusammenhang mit Speicherdruck analysieren. |
| `PLE_Trend_Collector_Proc.sql` | PLE-Trends über die Zeit sammeln. |

---

## 🧠 Query Store Hints: Hilfe bei instabilen Memory Grants

In SQL Server 2022 kannst du Optimizer-Hints **ohne Änderung am Anwendungscode** anwenden. So lassen sich übermäßige Memory Grants begrenzen, Pläne stabilisieren und das Verhalten des Optimizers beeinflussen.

```sql
EXEC sys.sp_query_store_set_hints
    @query_id = 12345,
    @value = N'OPTION(MAX_GRANT_PERCENT = 5)';
```

So machst du die Änderung rückgängig:

```sql
EXEC sys.sp_query_store_remove_hints @query_id = 12345;
```

---

## 📈 PLE als Trend statt als Einzelwert

Ein einzelner PLE-Wert sagt selten genug aus — entscheidend ist der **Trend**. Deshalb enthält das Repository einen Collector, der regelmäßig Werte misst und in `dbo.PLE_History` speichert.

So entsteht eine Verlaufshistorie des Speicherverhaltens, die du in Excel oder Grafana darstellen kannst.

```sql
EXEC dbo.CollectPLETrend @Samples = 120, @IntervalSeconds = 10;
```

---

## 🧭 Bewährte Vorgehensweisen

- Erweitere den RAM nicht, bevor du weißt, **wer ihn verbraucht**.
- Betrachte **PLE als Trend**, nicht als isolierten Wert.
- Überwache **Memory Clerks**, nicht nur den gesamten Speicherverbrauch.
- Auch der **Plan Cache** benötigt Speicher; sinnvolle Parametrisierung ist wichtig.
- Nutze **Query Store Hints**, wenn du Pläne beeinflussen möchtest, ohne den Anwendungscode zu ändern.

> „Performance beginnt damit zu verstehen, was den Arbeitsspeicher tatsächlich belegt.“

---

📘 Repository: [github.com/marcinpytlik/SQLManiak/tree/master/docs/MemoryInternals](https://github.com/marcinpytlik/SQLManiak/tree/master/docs/MemoryInternals)
