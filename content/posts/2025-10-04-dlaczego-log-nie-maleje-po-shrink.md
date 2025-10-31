---
title: "Dlaczego plik log nie maleje po SHRINK i co z tym zrobić"
date: "2025-10-04"
slug: "dlaczego-log-nie-maleje-po-shrink"
draft: false
description: "Masz wrażenie, że SHRINKFILE na pliku log nic nie daje? Tu jest kompletna mapa pułapek: VLF, otwarte transakcje, brak backupów logu i nieuśpione replikacje."
tags: ["SQL Server", "Transaction Log", "VLF", "Backup", "DBA"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/dlaczego-log-nie-maleje-po-shrink.png"
canonical: "https://sqlmaniak.blog/dlaczego-log-nie-maleje-po-shrink"
---

Lead
----
„Zrobiłem SHRINK i nic…”. Klasyka. Plik log nie zmaleje, jeśli *aktywny fragment logu* siedzi na końcu pliku albo masz otwarte transakcje. Rozplątujemy to krok po kroku.

## Szybka diagnoza
```sql
-- Aktywny log, VLF-y
DBCC LOGINFO;   -- w nowszych wersjach: sys.dm_db_log_info(DB_ID())

SELECT vlf_sequence_number, vlf_active, file_id FROM sys.dm_db_log_info(DB_ID())
ORDER BY vlf_sequence_number;
```

### Główne blokery shrinka
- Otwarte/długie transakcje (w tym „zapomniany” implicit tran w SSMS).  
- Brak łańcucha backupów logu (model FULL, ale brak `BACKUP LOG`).  
- Aktywne funkcje: replikacja, CDC, log shipping – „przytrzymują” log.  
- Zbyt wiele małych VLF (agresywny FILEGROWTH w KB).

## Procedura odzyskiwania miejsca
1) **Zrób BACKUP LOG** (model FULL/BULK_LOGGED).  
2) **Zamknij długie transakcje** – znajdź je:
```sql
SELECT s.session_id, r.start_time, r.status, r.command, r.wait_type, s.login_name, s.host_name
FROM sys.dm_exec_requests r
JOIN sys.dm_exec_sessions s ON s.session_id=r.session_id
WHERE r.database_id = DB_ID();
```
3) **Uśpij replikacje/CDC** jeśli to bezpieczne na okno.  
4) **Shrink kontrolowany**:
```sql
USE MyDb;
DBCC SHRINKFILE (MyDb_log, 102400); -- target w MB
```
5) **Ustaw sensowny FILEGROWTH** i bazowy rozmiar logu (np. 64–128 GB dla systemu z ciężkim OLTP, *empirycznie*).

## Porządek w VLF
- Sprawdź liczbę VLF; celuj w setki, nie dziesiątki tysięcy.
- Wyczyść: „cykl” BACKUP LOG → SHRINKFILE do sensownego rozmiaru → powiększ *jednym* skokiem.

```sql
-- Przykład: ustaw 64GB i growth 4GB
DBCC SHRINKFILE (MyDb_log, 1024); -- tymczasowe przycięcie
ALTER DATABASE MyDb MODIFY FILE (NAME=MyDb_log, SIZE=65536MB, FILEGROWTH=4096MB);
```

## Weryfikacja i monitoring
- `sys.dm_db_log_space_usage` i `sys.dm_db_log_stats(DB_ID())`.  
- W Grafanie obserwuj: `% used log`, liczbę VLF, częstotliwość autogrowth.

## Anti‑patterns
- Ciągłe SHRINK co noc — niszczy fragmentację VLF i wydajność.  
- FILEGROWTH w MB/KB: zbyt małe skoki → „tysiące VLF”.  
- Brak strategii backupu logu w modelu FULL.
