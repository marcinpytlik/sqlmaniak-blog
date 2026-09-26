---
title: "Wait Statistics — od czego naprawdę zacząć diagnozę wydajności SQL Server"
date: 2026-11-17T20:00:00+01:00
slug: wait-statistics-sql-server
description: "Jak czytać Wait Statistics w SQL Server, czego nie interpretować wprost i dlaczego delta waitów jest lepsza niż pojedynczy licznik od startu instancji."
tags: [SQLServer, WaitStats, Performance, Troubleshooting, DBA]
categories: [SQL Server]
draft: false
---

Wait Statistics nie odpowiadają na pytanie: „co jest zepsute?”.

Odpowiadają raczej: „na co SQL Server czekał?”.

## Aktualne waity instancji

```sql
SELECT TOP (30)
    wait_type,
    waiting_tasks_count,
    wait_time_ms,
    signal_wait_time_ms
FROM sys.dm_os_wait_stats
ORDER BY wait_time_ms DESC;
```

Ten wynik obejmuje okres od startu instancji lub wyczyszczenia statystyk. Bez kontekstu łatwo wyciągnąć błędne wnioski.

## Licz deltę

Lepsze podejście podczas incydentu:

1. pobierz stan A,
2. odczekaj określony czas,
3. pobierz stan B,
4. policz różnicę.

Interesuje Cię to, co wydarzyło się w czasie problemu.

## Waity i aktywne żądania

```sql
SELECT
    r.session_id,
    DB_NAME(r.database_id) AS DatabaseName,
    r.wait_type,
    r.wait_time,
    r.wait_resource,
    r.blocking_session_id,
    r.cpu_time,
    r.logical_reads
FROM sys.dm_exec_requests AS r
WHERE r.session_id <> @@SPID
ORDER BY r.wait_time DESC;
```

Dopiero wtedy wait type zaczyna mieć konkretne znaczenie.

## Przykładowe kierunki analizy

- `PAGEIOLATCH_*` — storage, duże skany, pamięć,
- `LCK_M_*` — blokowanie i transakcje,
- `RESOURCE_SEMAPHORE` — memory grants,
- `ASYNC_NETWORK_IO` — sposób odbierania danych przez klienta.

To kierunki diagnostyczne, nie gotowe diagnozy.

## Podsumowanie

Wait Statistics są mapą, nie odpowiedzią.

Spokojny DBA używa ich do zawężenia obszaru poszukiwań.