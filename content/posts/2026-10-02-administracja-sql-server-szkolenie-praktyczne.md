---
title: "Administracja SQL Server — 5-dniowe szkolenie praktyczne"
date: "2026-10-02"
slug: "administracja-sql-server-szkolenie-praktyczne"
draft: false
description: "Praktyczne 5-dniowe szkolenie z administracji SQL Server: instalacja, konfiguracja, storage, backup/restore, bezpieczeństwo, SQL Agent, monitoring, troubleshooting i podstawy performance."
tags: ["SQL Server", "Administracja", "DBA", "Backup", "Restore", "Monitoring", "Performance", "Szkolenia"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/administracja-sql-server-szkolenie-praktyczne/"
---

Dobra administracja SQL Server nie polega na tym, że serwis działa, backup job jest zielony, a dysk jeszcze ma wolne miejsce.

Administrator powinien rozumieć, **co dzieje się z instancją, bazami, logiem transakcyjnym, pamięcią, tempdb, backupami, jobami i użytkownikami** — oraz wiedzieć, gdzie szukać przyczyny, kiedy coś zaczyna działać inaczej niż powinno.

Właśnie z tego założenia powstało moje szkolenie **„Administracja SQL Server”** — pięć dni praktycznej pracy od instalacji i konfiguracji instancji, przez backup/recovery, bezpieczeństwo i automatyzację, aż do monitoringu, troubleshooting i podstaw diagnostyki wydajności.

To nie jest kurs polegający na przeklikiwaniu SQL Server Management Studio. Każdy temat kończy się praktyką i weryfikacją działania.

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone przede wszystkim dla:

- początkujących i średniozaawansowanych administratorów SQL Server,
- administratorów Windows, którzy przejmują odpowiedzialność za SQL Server,
- developerów pełniących również rolę DBA,
- osób utrzymujących aplikacje korzystające z SQL Server,
- zespołów, które chcą uporządkować standardy administracji instancjami SQL Server,
- osób przygotowujących się do samodzielnej pracy operacyjnej z SQL Server.

Uczestnik powinien znać podstawy relacyjnych baz danych i swobodnie pracować w środowisku Windows.

Znajomość podstaw T-SQL będzie pomocna, ale nie jest wymagane doświadczenie administratorskie.

## Jak wygląda szkolenie?

Każdy blok ma podobny rytm:

1. krótkie omówienie mechanizmu,
2. demonstracja prowadzącego,
3. samodzielne ćwiczenie,
4. sprawdzenie efektu,
5. kontrolowany problem albo niepoprawna konfiguracja,
6. diagnoza i naprawa.

W praktyce nacisk jest położony na zrozumienie **dlaczego coś działa** oraz **co zrobić, kiedy przestaje działać**.

## Program — 5 dni

### Dzień 1 — architektura, instalacja i konfiguracja SQL Server

Pierwszy dzień porządkuje fundamenty pracy administratora:

- architektura SQL Server Database Engine,
- instancja domyślna i nazwana,
- usługi SQL Server i SQL Server Agent,
- konta usług i podstawy service accounts,
- instalacja SQL Server,
- konfiguracja po instalacji,
- porty TCP i SQL Server Configuration Manager,
- konfiguracja pamięci,
- MAXDOP i Cost Threshold for Parallelism,
- pliki systemowych baz danych,
- model i msdb,
- tempdb,
- podstawowe ustawienia instancji,
- error log i podstawowe źródła diagnostyczne.

Już pierwszego dnia uczestnik uczy się odróżniać konfigurację „domyślną” od konfiguracji świadomej.

### Dzień 2 — storage, pliki baz danych, log transakcyjny i backup/restore

Drugi dzień skupia się na danych i odtwarzalności:

- pliki MDF/NDF/LDF,
- filegroups,
- autogrowth,
- rozmiar początkowy i pre-sizing,
- tempdb i jego pliki,
- recovery models,
- mechanika logu transakcyjnego,
- VLF,
- log_reuse_wait_desc,
- backup FULL,
- backup DIFF,
- backup LOG,
- COPY_ONLY,
- CHECKSUM i kompresja,
- restore,
- NORECOVERY i RECOVERY,
- point-in-time recovery,
- tail-log backup,
- weryfikacja historii backupów,
- test restore.

Jedna z najważniejszych zasad tego dnia brzmi:

**backup wykonany poprawnie nie oznacza jeszcze, że strategia odtwarzania działa.**

### Dzień 3 — bezpieczeństwo, SQL Server Agent i maintenance

Trzeciego dnia przechodzimy do codziennego utrzymania instancji:

- logins i users,
- server roles i database roles,
- mapowanie login → user,
- Windows Authentication i SQL Authentication,
- zasada least privilege,
- GRANT, DENY i REVOKE,
- orphaned users,
- SQL Server Agent,
- joby, kroki i harmonogramy,
- job ownership,
- Database Mail,
- alerty i operatory,
- maintenance,
- DBCC CHECKDB,
- indeksy i statystyki z perspektywy DBA,
- reorganize vs rebuild,
- aktualizacja statystyk,
- podstawy patchingu i aktualizacji SQL Server.

Celem nie jest budowa skomplikowanego systemu bezpieczeństwa, tylko zrozumienie, jak nie tworzyć zbędnych uprawnień i jak automatyzować codzienne operacje.

### Dzień 4 — monitoring i troubleshooting

Czwarty dzień jest poświęcony diagnozie.

Pracujemy między innymi z:

- aktywnymi sesjami i requestami,
- DMVs,
- blockingiem,
- deadlockami,
- wait statistics,
- CPU,
- pamięcią,
- I/O,
- tempdb,
- rosnącym logiem,
- błędami SQL Server Agent,
- SQL Server error log,
- Extended Events,
- podstawowymi licznikami Performance Monitor,
- Database Mail,
- monitoringiem połączeń i logowań.

Uczestnik nie dostaje gotowej odpowiedzi „co jest zepsute”.

Ma zebrać dane i zbudować hipotezę.

### Dzień 5 — podstawy performance i DBA Day

Ostatni dzień łączy codzienną administrację z podstawami performance troubleshooting:

- Query Store,
- najdroższe zapytania,
- plany wykonania z perspektywy administratora,
- indeksy brakujące i nadmiarowe,
- statystyki,
- parameter sniffing — wprowadzenie,
- plan cache,
- waits jako punkt startowy,
- podstawy capacity planning,
- checklisty operacyjne,
- procedury przed zmianą i po zmianie,
- backup przed maintenance,
- dokumentowanie środowiska,
- podstawy HA/DR i kiedy potrzebne jest FCI, AG albo Log Shipping.

Finałem jest **DBA Day** — zestaw kontrolowanych problemów wymagających samodzielnej diagnozy.

## DBA Day — zamiast idealnego środowiska

W końcowym scenariuszu środowisko przestaje być „laboratoryjnie poprawne”.

Uczestnik może dostać między innymi:

- niedziałający SQL Server Agent job,
- brak miejsca na dysku,
- źle skonfigurowany autogrowth,
- szybko rosnący log,
- brak backupu logu,
- blocking,
- deadlock,
- problem z loginem,
- użytkownika bez poprawnego mapowania,
- nieudany backup,
- błędny restore,
- problem z tempdb,
- wysokie waits,
- regresję zapytania widoczną w Query Store.

Celem nie jest odgadnięcie przyczyny.

Celem jest przejście przez proces:

**objaw → dane → hipoteza → weryfikacja → naprawa → potwierdzenie**

## Co uczestnik powinien umieć po szkoleniu?

Po pięciu dniach uczestnik powinien potrafić:

- poprawnie zainstalować i skonfigurować podstawową instancję SQL Server,
- ocenić najważniejsze ustawienia instancji,
- zarządzać plikami danych i logu,
- świadomie dobrać recovery model,
- wykonać backup i przeprowadzić restore,
- zweryfikować, czy środowisko jest odtwarzalne,
- zarządzać loginami, użytkownikami i rolami,
- tworzyć i diagnozować SQL Server Agent jobs,
- wykonywać podstawowe zadania maintenance,
- korzystać z CHECKDB,
- diagnozować blocking i deadlocki,
- korzystać z DMVs, wait statistics i Query Store,
- rozpoznać, kiedy problem wymaga dalszej analizy performance lub rozwiązania HA/DR,
- prowadzić podstawową dokumentację operacyjną środowiska.

## Czego to szkolenie świadomie nie obejmuje?

To szkolenie koncentruje się na **codziennej administracji SQL Server**.

Nie zastępuje osobnych, pogłębionych warsztatów z:

- Always On Availability Groups i FCI,
- Distributed AG i zaawansowanego Disaster Recovery,
- zaawansowanego performance tuningu,
- developmentu T-SQL,
- administracji Windows Server i Active Directory,
- Power BI i usług dodatkowych SQL Server.

Te tematy pojawiają się tylko w takim zakresie, w jakim administrator powinien rozumieć ich miejsce w architekturze.

## Forma organizacyjna

Szkolenie trwa **5 dni** i najlepiej sprawdza się jako zamknięty warsztat dla zespołu administrującego SQL Server lub osób przygotowujących się do samodzielnej pracy DBA.

Może być prowadzone stacjonarnie lub online.

Zakres może zostać dopasowany do wersji SQL Server używanej przez zespół oraz do jego aktualnego poziomu doświadczenia.

Pełny opis usług znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać środowisko, poziom zespołu oraz oczekiwany rezultat szkolenia.
