---
title: "Threadpool Waits – gdy zabraknie wątków"
date: 2025-10-31
slug: threadpool-waits
tags: [SQLServer, Waits, ThreadPool, Performance, Internals]
draft: false
---

SQL Server jest jak organizm oddychający wątkami.  
Każdy worker to oddech – bez nich system się dusi.  

Gdy zobaczysz `THREADPOOL` w `sys.dm_os_wait_stats`, wiesz, że SQL Server **walczy o tlen**.  
To nie jest zwykły wait — to moment, w którym silnik nie jest w stanie przydzielić nowych workerów,  
bo wszystkie dostępne wątki zostały pochłonięte przez równoległe zadania lub blokady.

---

## 🔍 Zajrzyj w DMV

```sql
-- sprawdź obciążenie puli wątków
SELECT scheduler_id, current_tasks_count, runnable_tasks_count, active_workers_count, work_queue_count
FROM sys.dm_os_schedulers
WHERE scheduler_id < 255;
```

📊 **Interpretacja:**
- `current_tasks_count` – ile zadań zostało przydzielonych,  
- `runnable_tasks_count` – ile *czeka* na wątek,  
- `active_workers_count` – ilu workerów faktycznie pracuje,  
- `work_queue_count` – ile zapytań czeka w kolejce do schedulera.  

Jeśli `runnable_tasks_count > 0` dla wielu schedulerów, a `THREADPOOL` rośnie w `sys.dm_os_wait_stats`,  
serwer zaczyna się dusić.

---

## ⚙️ Co to znaczy w praktyce

Każdy SQL Server ma **ograniczoną pulę wątków** – zarządzaną przez **SOS Scheduler**.  
Gdy liczba jednoczesnych zapytań przekroczy możliwości schedulera,  
nowe sesje muszą *czekać na wolny worker thread*.  

Zazwyczaj prowadzi to do lawiny objawów:
- sesje wiszą w stanie `SUSPENDED`,  
- brak CPU usage mimo dużej liczby aktywnych połączeń,  
- blokady łańcuchowe i dramatyczne spowolnienie całego systemu.

---

## 🧠 Jak sprawdzić, czy to naprawdę `THREADPOOL`

```sql
-- czekające zapytania i typy WAIT
SELECT
    r.session_id,
    r.status,
    r.wait_type,
    r.scheduler_id,
    r.cpu_time,
    r.total_elapsed_time,
    t.text AS QueryText
FROM sys.dm_exec_requests AS r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) AS t
WHERE r.wait_type = 'THREADPOOL';
```

Jeśli w wynikach widzisz wiele sesji z tym samym typem WAIT,  
to znak, że SQL Server przekroczył limit workerów.

---

## 🧩 Co można z tym zrobić

1️⃣ **Zidentyfikuj, kto konsumuje wątki:**
   - długie zapytania równoległe (`CXPACKET`, `CXCONSUMER`),  
   - zablokowane sesje, które nigdy nie kończą transakcji,  
   - procedury systemowe działające w pętli (np. joby lub kursory).

2️⃣ **Zredukuj równoległość:**
   - ustaw `max degree of parallelism` (MAXDOP) na 4–8,  
   - obniż `cost threshold for parallelism` (jeśli zbyt niskie, zwiększ).  

3️⃣ **Oczyść połączenia i joby:**
   - sprawdź, czy aplikacje zamykają połączenia,  
   - przejrzyj joby SQL Agent – czasem zawieszony job blokuje schedulery.

4️⃣ **Monitoruj schedulery:**
   - `sys.dm_os_schedulers` – stan kolejki,  
   - `sys.dm_os_workers` – użycie workerów,  
   - `sys.dm_os_waiting_tasks` – aktywne oczekiwania.

---

## 📈 Szybki test równowagi

```sql
-- Zlicz ilu workerów działa względem limitu
SELECT COUNT(*) AS ActiveWorkers
FROM sys.dm_os_workers
WHERE state = 'RUNNING';
```

Jeśli liczba aktywnych workerów zbliża się do limitu,  
SQL Server nie ma już czym oddychać.

---

## 💡 SQLManiak – Filozofia wydajności

> „Przeciążony system to system, który zapomniał oddychać.”  
> — *SQLManiak*

W SQL Serverze i w życiu — **równowaga wątków** to równowaga energii.  
Zbyt wiele równoległych myśli potrafi zablokować cały proces.

---

#SQLServer #ThreadPool #Waits #Performance #Internals #SQLManiak
