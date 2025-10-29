---
title: "Wewnętrzne mechanizmy pamięci SQL Server – co się dzieje w Buffer Pool"
date: 2025-10-22
slug: memory-internals
tags: [SQLServer, Internals, Memory, Performance, DBA]
draft: false
---

Za każdą operacją stoi pamięć: **Buffer Pool**, **Memory Clerks**, **Lazy Writer** i **PLE (Page Life Expectancy)**.  
To serce SQL Servera – a każdy spadek PLE to zawał.  
Zrozumienie, jak SQL zarządza stronami danych, to klucz do prawdziwego tuningu.

> „Co nie zmieści się w pamięci, wróci po zemstę z dysku.”

---

## 🧠 Architektura pamięci SQL Server

SQL Server ma własny system zarządzania pamięcią – niezależny od systemu operacyjnego.  
Dzięki temu może reagować szybciej i bardziej precyzyjnie na obciążenie.  

Najważniejsze komponenty:

| Obszar | Opis |
|--------|------|
| **Buffer Pool** | Przechowuje strony danych (8 KB) – główny cache odczytów/zapisów. |
| **Plan Cache** | Skompilowane plany zapytań – zbyt duży zabiera miejsce Buffer Poolowi. |
| **Memory Clerks** | Zarządzają przydziałami pamięci dla poszczególnych subsystemów. |
| **Workspace Memory** | Tymczasowa pamięć dla sortów, hash joinów i grupowań. |
| **Stolen Memory** | Pamięć „pożyczona” z Buffer Pool dla zapytań wykonawczych. |

---

## 🔄 Jak SQL Server zarządza stronami

Każda strona danych przechodzi swój cykl życia:

1. **Physical Read** – strona trafia z dysku do Buffer Pool.  
2. **Use in Query** – zapytanie korzysta z danych w pamięci.  
3. **Dirty Page** – strona jest zmodyfikowana, ale jeszcze nie zapisana.  
4. **Checkpoint / Lazy Writer** – zapisuje zmiany na dysk.  
5. **Eviction (LRU)** – gdy pamięć jest potrzebna, stare strony są usuwane.

W tle działa **LRU (Least Recently Used)**, który decyduje, które strony zostaną zwolnione.  

---

## 📊 Kluczowe wskaźniki

| Wskaźnik | Znaczenie |
|-----------|-----------|
| **Page Life Expectancy (PLE)** | Ile sekund średnio strona żyje w pamięci. Niski PLE = presja pamięciowa. |
| **Lazy Writes/sec** | Ile stron na sekundę usuwa Lazy Writer. |
| **Memory Grants Pending** | Zapytania czekające na przydział pamięci. |
| **Target vs Total Server Memory** | Czy SQL osiąga przydzielony limit RAM. |
| **Memory Clerks** | Kto faktycznie zjada pamięć (np. Buffer Pool, Query Execution, Lock Manager). |

---

## 🧩 Diagnostyka krok po kroku

📁 W repo znajdziesz skrypty gotowe do użycia:

| Skrypt | Opis |
|--------|------|
| `Target_vs_Total_Server_Memory.sql` | Porównanie przydzielonej i używanej pamięci. |
| `BufferPool_PLE_Counters.sql` | Trend PLE per NUMA node. |
| `Memory_Clerks_Overview.sql` | Kto najbardziej konsumuje pamięć. |
| `Memory_Grants_Status.sql` | Które zapytania czekają na granty. |
| `LazyWriter_Checkpoint_Stats.sql` | Aktywność w tle. |
| `BufferPool_ModifiedPages.sql` | Brudne strony per baza. |
| `Waits_Memory_Pressure.sql` | Potwierdzenie presji pamięciowej przez waity. |
| `PLE_Trend_Collector_Proc.sql` | Zbieranie trendu PLE w czasie. |

---

## 🧠 Query Store Hints – sposób na niestabilne granty

W SQL Server 2022 możesz wymuszać wskazówki optymalizatora **bez zmiany kodu**.  
Dzięki temu można ograniczyć zbyt duże granty pamięci, stabilizować plan i kontrolować zachowanie optymalizatora.

```sql
EXEC sys.sp_query_store_set_hints
    @query_id = 12345,
    @value = N'OPTION(MAX_GRANT_PERCENT = 5)';
```

Aby cofnąć zmianę:
```sql
EXEC sys.sp_query_store_remove_hints @query_id = 12345;
```

---

## 📈 PLE jako trend, nie liczba

Jednorazowy odczyt PLE nic nie znaczy – liczy się **trend**.  
Dlatego w repo znajdziesz prosty kolektor, który zbiera dane co kilka sekund i zapisuje w tabeli `dbo.PLE_History`.

Wynik to żywa historia pamięci – możesz wykreślić trend w Excelu lub Grafanie.

```sql
EXEC dbo.CollectPLETrend @Samples = 120, @IntervalSeconds = 10;
```

---

## 🧭 Dobre praktyki

- Nie zwiększaj RAM zanim zrozumiesz, **kto go zjada**.  
- Traktuj **PLE jako trend**, nie pojedynczą wartość.  
- Obserwuj **Memory Clerks**, nie tylko ogólny użytek.  
- **Plan cache** też zjada pamięć – parametryzacja to podstawa.  
- Używaj **Query Store Hints** do kontroli planów, gdy kod nie jest Twój.  

> „Wydajność zaczyna się od zrozumienia, kto naprawdę zajmuje pamięć.”

---

📘 Repo: [github.com/marcinpytlik/SQLManiak/tree/master/docs/MemoryInternals](https://github.com/marcinpytlik/SQLManiak/tree/master/docs/MemoryInternals)
