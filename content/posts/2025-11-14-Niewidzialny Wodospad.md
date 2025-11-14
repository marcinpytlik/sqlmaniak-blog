---
title: '"Niewidzialny Wodospad" – Jak monitorować i rozwiązywać rywalizację o I/O w SQL Server'
date: 2025-11-14
tags:
  - SQL Server
  - SQL Server 2022
  - Monitoring
  - Performance
  - I/O
categories:
  - SQLManiak
draft: false
---

"Niewidzialny Wodospad" – Jak monitorować i rozwiązywać rywalizację o I/O w SQL Server
W SQL Server pod maską działa fascynująca choreografia kluczowych procesów tła, które decydują o wydajności. Chociaż Checkpoint, Lazy Writer i Log Flush mają różne zadania, wszystkie rywalizują o ten sam kluczowy zasób: podsystem I/O, którym zarządza I/O Scheduler.

Zrozumienie ich interakcji jest kluczowe, a my możemy ją "uwidocznić" za pomocą DMV i Extended Events (XE).

Klucz do zrozumienia: I/O Synchroniczne vs Asynchroniczne
Aby zrozumieć "wodospad", musimy rozróżnić dwa typy zapisów I/O, o które walczą te procesy:

I/O Synchroniczne (Krytyczne): To głównie Log Flush (wait WRITELOG). Sesja użytkownika, która wykonuje COMMIT, musi fizycznie poczekać na zakończenie tego zapisu. To jak rozmowa telefoniczna – musisz czekać na odpowiedź.

I/O Asynchroniczne (Tła): To Checkpoint i Lazy Writer. SQL Server zleca zapis i nie czeka na jego ukończenie; sesja użytkownika działa dalej. To jak wysłanie e-maila – serwer zajmie się dostarczeniem w tle.

Problem "Wodospadu" polega na tym, że asynchroniczne I/O (Checkpoint) staje się tak intensywne, że zapycha cały podsystem dyskowy. Przez to, krytyczne I/O synchroniczne (Log Flush) musi stać w tej samej "zakorkowanej" kolejce i dramatycznie zwalnia.

Co monitorować?
Monitorowanie każdego z tych elementów osobno nie da pełnego obrazu. Kluczem jest obserwowanie ich jednocześnie.

1. Checkpoint
Zapisuje "brudne" strony danych (MDF/NDF), aby skrócić czas odzyskiwania bazy.

Jak monitorować: sys.dm_db_log_stats (log_bytes_to_checkpoint) oraz checkpoint_end (XE).

Na co uważać: Intensywne checkpointy mogą saturować I/O, co rykoszetem uderza we wszystkie inne operacje, w tym zapisy logu.

2. Lazy Writer
Gdy brakuje pamięci w buforze, budzi się, by zwolnić miejsce (zapisując "brudne" strony lub wyrzucając "czyste").

Jak monitorować: Licznik Buffer Manager: Lazy writes/sec (sys.dm_os_performance_counters).

Na co uważać: Wysoka aktywność wskazuje na presję na pamięć (Memory Pressure) i generuje dodatkowe, "nieplanowane" I/O zapisu.

3. Log Flush (Zapisy Logu Transakcyjnego)
Serce operacji INSERT/UPDATE/DELETE. Każdy COMMIT czeka na fizyczny zapis na dysk (LDF).

Jak monitorować: sys.dm_io_virtual_file_stats (write_latency_ms dla pliku LDF) oraz wait_info (XE) dla WRITELOG.

Na co uważać: Wysokie opóźnienia (WRITELOG) bezpośrednio spowalniają każdą modyfikację danych.

4. I/O Scheduler (Statystyki Oczekiwań)
Tablica wyników, na której widać efekt rywalizacji o dysk.

Jak monitorować: sys.dm_os_wait_stats (agregat) lub wait_info (XE) (w czasie rzeczywistym).

Na co uważać: Wysokie czasy dla WRITELOG, PAGEIOLATCH_SH/EX/UP (czekanie na strony danych) oraz ASYNC_IO_COMPLETION (ogólne I/O w tle, często checkpoint).

Dlaczego "Niewidzialny Wodospad"?
Jeden proces rozpoczyna kaskadę zdarzeń, które spiętrzają się, tworząc problem:

Duża modyfikacja danych generuje tysiące "brudnych" stron.

Uruchamia się Checkpoint, by zapisać te strony (masowe I/O asynchroniczne).

Podsystem I/O zostaje obciążony.

W tym samym czasie, inne transakcje próbują się zatwierdzić (COMMIT), co wymaga Log Flush (krytyczne I/O synchroniczne).

Operacje Log Flush zwalniają, bo czekają w tej samej kolejce co Checkpoint. Czasy WRITELOG rosną.

Jeśli dodatkowo brakuje pamięci, Lazy Writer też dokłada swoje zapisy do tej samej, zakorkowanej kolejki.

Inne popularne źródła "Wodospadu"
Ten sam efekt rywalizacji o I/O mogą wywołać inne operacje:

Index Rebuild: Generuje jednocześnie masowy odczyt (stary indeks), masowy zapis (nowy indeks) ORAZ intensywne zapisy logu (Log Flush).

Backup (Full/Diff): Generuje potężne Read I/O na plikach danych, rywalizując z zapytaniami użytkowników, które też chcą czytać dane (PAGEIOLATCH_SH).

Autogrowth (Rozrost plików): Nagły rozrost pliku MDF lub LDF potrafi "zamrozić" zapisy na czas jego trwania, powodując podobne objawy.

Jak to zademonstrować?
Obciążenie: Wygeneruj duże obciążenie INSERT/UPDATE w jednej sesji. Jednocześnie w drugiej sesji wykonuj małe, szybkie transakcje z COMMIT.

Extended Events (XE): Uruchom sesję łapiącą checkpoint_end, log_flush_complete oraz wait_info (filtrowane na WRITELOG, PAGEIOLATCH_* z czasem trwania > 0).

Analiza: Obserwuj na żywo, jak moment rozpoczęcia checkpoint_end koreluje ze skokowym wzrostem czasów wait_info dla WRITELOG.

Głębsza analiza: Kto na tym cierpi? (Query Store)
Gdy już wiesz, że masz problem (np. wysokie WRITELOG), musisz wiedzieć, kto cierpi najbardziej.

Otwórz Query Store w Management Studio.

Znajdź raport "Top Resource Consuming Queries".

Zmień metrykę z domyślnej (CPU) na "Total Wait Time" (Całkowity czas oczekiwania).

Teraz posortuj zapytania. Zobaczysz, że ten "infrastrukturalny" problem "wodospadu" najbardziej uderza w konkretne zapytania UPDATE lub procedury INSERT, które spędzają najwięcej czasu, czekając na WRITELOG lub PAGEIOLATCH.

🎯 Jak rozwiązać lub złagodzić ten problem?
Samo monitorowanie nie wystarczy. Oto konkretne kroki naprawcze:

1. Rozwiązanie problemu Checkpointu (Indirect Checkpoint)
Od SQL Server 2016 domyślnym trybem jest Indirect Checkpoint. Działa on w oparciu o docelowy czas odzyskiwania (TARGET_RECOVERY_TIME), a nie liczbę logu.

Efekt: Zamiast jednego, potężnego "wodospadu" co minutę, SQL Server wykonuje serię małych, ciągłych "strumyczków" zapisu I/O. To radykalnie wygładza obciążenie dysków i zmniejsza szansę na zakorkowanie kolejki dla Log Flush.

Akcja: Upewnij się, że Twoje bazy mają ustawiony TARGET_RECOVERY_TIME (np. na 60 sekund).

2. Rozwiązanie problemu Log Flush (Separacja I/O)
To absolutna podstawa.

Efekt: Fizyczne oddzielenie plików LDF od plików MDF/NDF sprawia, że Checkpoint (zapisujący na dyski z MDF) i Log Flush (zapisujący na dysk z LDF) nie rywalizują ze sobą o ten sam zasób.

Akcja: Umieść pliki logu transakcyjnego (LDF) na najszybszym możliwym nośniku (np. NVMe), który jest fizycznie odseparowany od dysków na pliki danych.

3. Rozwiązanie problemu Lazy Writera (Presja na pamięć)
Nadmierna aktywność Lazy Writera to niemal zawsze objaw, a nie przyczyna.

Efekt: Zmniejszenie presji na pamięć sprawia, że Lazy Writer nie musi tak agresywnie pracować i generować dodatkowego I/O.

Akcja: Dołóż RAM do serwera lub zoptymalizuj zapytania/indeksy, aby zużywały mniej pamięci (np. eliminując wielkie skany tabel).

Dashboard (np. w Grafanie)
Aby widzieć to na co dzień, zwizualizuj:

Opóźnienia Log Flush (średni czas WRITELOG)

Czasy zapisów dla plików danych (z sys.dm_io_virtual_file_stats)

Liczba i czas trwania checkpointów (z checkpoint_end XE)

Aktywność Lazy Writer (Lazy writes/sec)

Kluczowe statystyki oczekiwań (Wait Stats)
