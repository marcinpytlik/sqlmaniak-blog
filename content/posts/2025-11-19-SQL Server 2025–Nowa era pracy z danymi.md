---
title: "SQL Server 2025 – Nowa era pracy z danymi"
date: 2025-11-19
tags:
  - SQL Server
  - SQL Server 2025
  - Performance
  - Monitoring
  - Security
  - Query Store
  - JSONB
categories:
  - SQLManiak
draft: false
---

Premiera SQL Server 2025 przynosi zestaw zmian, które realnie wpływają na codzienną pracę administratorów, architektów oraz deweloperów baz danych. To nie jest edycja typu „poprawki i kosmetyka”. To największy krok naprzód od czasu SQL Server 2019 i 2022 – szczególnie w obszarze automatycznej optymalizacji, bezpieczeństwa oraz obserwowalności.

Poniżej znajduje się przegląd najważniejszych nowości, które faktycznie robią różnicę w środowiskach produkcyjnych.

---

## Adaptive Workload Intelligence (AWI)

SQL Server 2025 wprowadza moduł **Adaptive Workload Intelligence**.  
To rozbudowana warstwa predykcyjnej optymalizacji, która:

- wykrywa zbliżającą się presję na CPU, I/O lub log,
- dynamicznie dostosowuje strategie optymalizacji zapytań,
- moduluje memory granty w czasie rzeczywistym,
- zmienia priorytety I/O w zależności od typu obciążenia.

To kolejny krok po Memory Grant Feedback i Parameter Sensitive Plan – tym razem silnik zaczyna przewidywać, zanim problem wystąpi.

---

## Query Store 3.0 – pełna obserwowalność

Nowa wersja Query Store rozwiązuje jeden z największych braków poprzednich edycji – analizę zachowania planów w kontekście presji systemowej.

Najważniejsze nowości:

- **Capture on Pressure** – automatyczna rejestracja planów przy skokach obciążenia.
- **Historyczne baseline’y** – możliwość porównania każdego zapytania do dowolnego momentu w przeszłości.
- **Plan Graph Explorer** – wizualizacja ewolucji planów bez zewnętrznych narzędzi.

To narzędzie wreszcie staje się pełnoprawnym rejestratorem życia aplikacji.

---

## Instant Recovery 2.0 (ADR ulepszony)

Ulepszenia mechanizmu Accelerated Database Recovery:

- szybsze redukowanie aktywnych transakcji po awarii,
- krótszy czas REDO/UNDO,
- nowe DMV ujawniające, które transakcje i strony najbardziej spowalniają recovery.

W scenariuszach HA różnica jest zauważalna natychmiast.

---

## Log V2 – inteligentny dziennik transakcyjny

W SQL Server 2025 log transakcyjny dostał największą zmianę od lat:

- dynamiczna alokacja VLF w zależności od obciążenia,
- redukcja fragmentacji logu,
- zoptymalizowany algorytm flushowania dostosowany do przepustowości dysków,
- nowe DMV: `sys.dm_db_log_pressure_stats`.

Efekt: wyraźnie mniejsza presja na log w systemach o dużym wolumenie zapisów.

---

## Security Shield – nowa warstwa bezpieczeństwa

SQL Server 2025 idzie mocno w stronę architektury „zero trust”.

Najważniejsze nowości:

- **Secure Credential Vault** – zaszyfrowany magazyn poświadczeń dla obiektów zewnętrznych.
- **Row Access Policies 2.0** – szybsze, elastyczniejsze reguły oparte na expression trees.
- **Wymuszanie TDS Encryption** – automatyczna walidacja zgodności protokołu.

To najbardziej rozbudowana warstwa bezpieczeństwa w historii SQL Server.

---

## TempDB Evolution – koniec klasycznych konfliktów

Modernizacja TempDB obejmuje:

- globalny cache stron współdzielony pomiędzy plikami,
- poprawione algorytmy alokacji HOBT,
- wyraźne ograniczenie PAGELATCH contention (nawet 40–70%).

Wreszcie poprawa, którą można odczuć bez dodatkowych trace flag.

---

## Native JSONB

SQL Server 2025 wprowadza **JSONB** – binarną wersję JSON:

- kolumny typu JSONB,
- indeksy podobne do GIN,
- operatorowe zapytania na strukturach JSON,
- pełne wsparcie dla transakcyjnego ładowania i zapisu.

To funkcjonalność, o którą środowisko prosiło od wielu lat.

---

## Columnstore Genie

Rozszerzenia silnika analitycznego obejmują:

- nowy tryb kompresji LZ4+,
- dynamiczne scalanie małych rowgroups,
- rekomendacje indeksów columnstore generowane automatycznie na podstawie Query Store.

Analiza danych staje się zauważalnie szybsza i lżejsza.

---

## Konteneryzacja i ARM64

Nowości dla środowisk DevOps i CI/CD:

- oficjalne kontenery SQL Server na ARM64,
- wsparcie dla AG w środowiskach kontenerowych (cluster-less),
- sidecar monitoring z natywną obsługą.

To ułatwia budowanie lekkich środowisk developerskich.

---

## Nowe DMV, XE i narzędzia diagnostyczne

SQL Server 2025 dostarcza obszerny zestaw nowych narzędzi obserwowalności:

- `sys.dm_os_page_life_cycle` – analiza życia stron,
- `sys.dm_exec_batch_mode_feedback` – feedback dla trybu batchowego,
- nowe zdarzenia XE dla flush logu, checkpoint pipeline, latch contention,
- kategoria XE: **Pressure Explorer**.

To fundament do budowania własnych monitorów SLO/SLA bez narzędzi komercyjnych.

---

## Podsumowanie

SQL Server 2025 jest dużym krokiem naprzód.  
Nowe mechanizmy adaptacyjne, rozbudowana obserwowalność oraz udoskonalony log i TempDB znacząco zwiększają stabilność oraz przewidywalność działania silnika.

Najważniejsze obszary zmian:

1. **Automatyzacja i inteligentna adaptacja obciążeń**  
2. **Widoczność i diagnostyka** (Query Store 3.0, nowe DMV, XE)  
3. **Bezpieczeństwo i architektura zero trust**  
4. **Nowoczesne typy danych i funkcje dla deweloperów** (JSONB)  
5. **Pełna gotowość na konteneryzację i ARM64**

SQL Server 2025 to wersja, która zmienia sposób myślenia o wydajności, skalowalności i monitoringu.
