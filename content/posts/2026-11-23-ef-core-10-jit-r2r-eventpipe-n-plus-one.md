---
title: "EF Core oczami DBA: czy JIT uratuje N+1? .NET 10, ReadyToRun i EventPipe"
date: 2026-11-23T08:00:00+01:00
slug: "ef-core-10-jit-readytorun-eventpipe-n-plus-one"
description: "Kontynuacja laboratorium EF Core 10 i SQL Server 2022: 640 pomiarów podczas profilowania JIT, ReadyToRun, Composite i No-tiering. dotnet-counters, dotnet-trace, GC, alokacje i granice interpretacji."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - EF Core
  - .NET 10
  - Query Store
  - JIT
  - ReadyToRun
  - EventPipe
  - performance tuning
  - ORM
draft: false
---

# EF Core oczami DBA: czy JIT uratuje N+1? .NET 10, ReadyToRun i EventPipe

**Jeżeli ta sama operacja EF Core wykonuje 101 poleceń SQL zamiast jednego, to czy szybsza kompilacja .NET potrafi zniwelować różnicę?**

To pytanie zostało ze mną po [poprzednim artykule o N+1, Include, Projection, SplitQuery i Query Store](/posts/ef-core-n-plus-one-include-projection-split-query-query-store/). Tam przy identycznych danych **100 zamówień i 1000 pozycji** otrzymałem mediany **119,83 ms dla N+1** i **5,11 ms dla Projection**. Po stronie SQL Server różnica wyniosła **1103 kontra 14 logical reads** na żądanie.

Teraz idę dalej, ale nie zmieniam zapytań ani schematu danych. Zmieniam **sposób publikacji aplikacji .NET 10**, obserwuję proces przez `dotnet-counters` i `dotnet-trace`, a wyniki zestawiam z wcześniejszymi obserwacjami Query Store.

Nie szukam zwycięzcy za wszelką cenę. Chcę ustalić, **co naprawdę da się wywnioskować z liczników CLR, kiedy SQL Server wykonuje tę samą pracę**.

**Kod, skrypty i dokumentacja: [WWSI_CSharp — Demo 67, EF Core Performance Lab](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).** Szczegółowe tabele i zastrzeżenia znajdują się także w [raporcie końcowym eksperymentu 03](https://github.com/marcinpytlik/WWSI_CSharp/blob/main/demonstracje/67_EfCorePerformanceLab/experiments/03_Compilation/FINAL-REPORT-2026-11-22.md).

## Najpierw przypomnienie: co jest stałe?

Aplikacja wykorzystuje **ASP.NET Core / .NET 10, EF Core 10 i SQL Server 2022 Developer** w kontenerach Linux. W bazie `EfPerformanceLab` znajduje się 100 zamówień, każde z 10 pozycjami.

Cztery endpointy zwracają te same DTO; zgodność wyników sprawdza automatyczny test. Każdy wariant korzysta z `AsNoTracking()`.

| Strategia | Jak pobiera dane | Polecenia SQL na żądanie |
|---|---|---:|
| N+1 | Zamówienia, potem osobny SELECT pozycji dla każdego zamówienia | **101** |
| Include | `Include()` i `AsSingleQuery()` | **1** |
| Projection | `Select()` bezpośrednio do DTO | **1** |
| SplitQuery | `Include()` i `AsSplitQuery()` | **2** |

Wariant N+1 jest **celową implementacją antywzorca**, a nie przypadkowym skutkiem lazy loading. Właśnie dlatego pozwala odtworzyć problem, zamiast liczyć na to, że zostanie wywołany przez konkretną konfigurację nawigacji.

Z perspektywy DBA ważna jest liczba operacji, którą generuje **jedno żądanie biznesowe**, a nie tylko koszt pojedynczego SELECT-a.

## Cztery sposoby uruchomienia tej samej aplikacji

W osobnym eksperymencie publikacji przygotowałem cztery warianty. Wszystkie wykorzystują **Release, linux-x64 i self-contained**. Dla Composite ReadyToRun warunek self-contained jest szczególnie istotny.

| Tryb | Ustawienie publikacji / runtime | Tiered Compilation |
|---|---|---|
| `jit` | `PublishReadyToRun=false` | Włączona |
| `r2r` | `PublishReadyToRun=true` | Włączona |
| `composite` | `PublishReadyToRunComposite=true` | Włączona |
| `no-tiering` | Publikacja jak `jit`, `TieredCompilation=0` | Wyłączona |

Wariant `no-tiering` nie jest kolejną technologią kompilacji. Zmieniam w nim sposób działania runtime: wyłączam kompilację warstwową, co może zmienić kompromis między kosztem kompilacji a jakością wykonywanego kodu.

Podstawą odróżnienia tych efektów była wcześniejsza faza **03B**: cztery zrównoważone rundy zmieniające kolejność wariantów, po 10 powtórzeń każdej strategii. Łącznie było to **4 rundy × 4 tryby × 4 strategie × 10 powtórzeń = 640 próbek aplikacyjnych**. Następna faza **03C** odczytywała wskaźniki całego procesu (CPU, alokacje, kolekcje GC). W tym artykule pokazuję przede wszystkim fazę **03D** — osobny eksperyment z narzędziami EventPipe.

To ważne rozróżnienie: **640 próbek z etapu 03B i 640 próbek z etapu 03D to różne zbiory**, uzyskane w innych warunkach.

## Jak podłączyłem EventPipe do procesu w Dockerze?

Aplikacja pracuje w obrazie runtime, a narzędzia diagnostyczne umieściłem w **oddzielnym kontenerze `profiler`**, opartym na .NET SDK 10.

W Docker Compose kontener profilera współdzieli z API:

- przestrzeń PID (`pid: "service:api"`);
- wolumen `/tmp`, w którym .NET udostępnia gniazdo diagnostyczne.

Dzięki temu `dotnet-counters ps` widzi proces aplikacji, a narzędzia dołączają do niego bez instalowania SDK w obrazie produkcyjnym API.

Przykładowe polecenia zbierania danych wewnątrz kontenera:

```bash
/tools/dotnet-counters collect \
    --process-id 1 \
    --refresh-interval 1 \
    --format csv \
    --counters System.Runtime \
    --output /output/jit-counters.csv
```

```bash
/tools/dotnet-trace collect \
    --process-id 1 \
    --profile dotnet-common,dotnet-sampled-thread-time \
    --output /output/jit-trace.nettrace
```

**Nie uruchamiam obu profilerów jednocześnie.** Każde narzędzie otrzymuje osobną serię żądań. Ślady dotyczą procesu **po uruchomieniu i rozgrzaniu aplikacji**; nie mierzą zimnego startu CLR ani całkowitego początkowego kosztu JIT.

W fazie 03D wykonałem dla każdego trybu po **20 powtórzeń czterech strategii** w sesji `dotnet-counters` oraz kolejne 20 powtórzeń w sesji `dotnet-trace`. To razem:

**4 tryby × 4 strategie × 20 powtórzeń × 2 rodzaje zbierania = 640 pomiarów operacji EF Core.**

Przed właściwą serią test potwierdzał zwracane dane oraz liczbę poleceń SQL: **101 / 1 / 1 / 2**.

## Czasy podczas profilowania: N+1 nadal wyraźnie odstaje

Poniżej wyniki **median czasu samej operacji EF Core**, a nie pełnego HTTP ani CPU SQL Server.

### Sesja z `dotnet-counters` — mediana w ms

| Strategia | JIT | R2R | Composite R2R | Bez tieringu |
|---|---:|---:|---:|---:|
| **N+1** | **135,13** | **177,27** | **136,99** | **169,22** |
| Include | 6,27 | 7,39 | 6,64 | 9,79 |
| Projection | **5,76** | 6,75 | 6,09 | 6,20 |
| SplitQuery | 6,46 | 6,67 | 6,55 | 7,71 |

### Sesja z `dotnet-trace` — mediana w ms

| Strategia | JIT | R2R | Composite R2R | Bez tieringu |
|---|---:|---:|---:|---:|
| **N+1** | **137,43** | **145,46** | **142,01** | **178,11** |
| Include | 8,00 | 7,35 | 8,51 | 11,06 |
| Projection | **6,05** | 6,66 | 6,89 | 7,48 |
| SplitQuery | 6,67 | **6,17** | 6,52 | 7,66 |

Najbardziej widoczna obserwacja nie dotyczy R2R. **We wszystkich zmierzonych trybach N+1 pozostaje o rząd wielkości wolniejszy niż pozostałe strategie.** W sesji JIT z `dotnet-counters` stosunek median N+1 do Projection wyniósł około **23,5:1**.

Nie oznacza to, że JIT jest „z definicji lepszy” od ReadyToRun. To **lokalne mediany z sesji profilowania wykonanych w określonej kolejności**. Koszt diagnostyki wpływa na badany proces, a ta faza nie była kontrbalansowana.

Jeśli chcę mówić o powtarzalności wpływu trybu kompilacji, muszę wrócić do osobnych, zrównoważonych rund **03B**, a nie wybierać najmniejszą liczbę z tabeli 03D.

## Co pokazują liczniki System.Runtime?

Od czterech wartości median przeszedłem do metryk **całego procesu API**. Oto zestawienie sesji z `dotnet-counters`:

| Metryka | JIT | R2R | Composite | Bez tieringu |
|---|---:|---:|---:|---:|
| Alokacje procesu, MB* | 124,4 | 123,0 | 124,0 | 125,3 |
| Czas JIT, s* | 3,04 | 2,92 | 2,86 | 0,04 |
| Liczba metod kompilowanych przez JIT* | 3752 | 3278 | 2808 | 63 |
| CPU user, s* | 4,84 | 5,16 | 4,86 | 3,05 |
| Mediana Working Set, MB | 185,4 | 188,7 | 199,3 | 164,3 |
| Liczba kolekcji Gen0* | 7 | 7 | 8 | 8 |

\* Wartości zagregowane z czasowych próbek liczników (`System.Runtime`, około 1 s) mają charakter **przybliżony**; ich interpretacja zależy od semantyki konkretnego licznika. Nie są pomiarem jednego wywołania EF Core.

Wariant `no-tiering` zgłosił w trakcie przechwytywania znacznie mniejszą aktywność kompilacji JIT. Mimo to jego mediany były przeważnie wyższe niż w pozostałych trybach.

To dobra przestroga przed prostym rozumowaniem:

> Mniej czasu poświęconego na JIT nie musi oznaczać mniejszej latencji operacji w już działającej aplikacji.

Ale **nie jest to dowód związku przyczynowego**. Mogły wpłynąć na to jakość kodu, stan procesu, rozgrzewka, kolejność testów i dodatkowy koszt profilowania. Nie mamy podstaw, żeby z tej tabeli wyprowadzić uniwersalną rekomendację wyłączenia lub włączenia tieringu.

### A co z GC i pamięcią?

W pokazanych seriach łączna przybliżona wielkość alokacji procesu pozostawała zbliżona — około **123–125 MB**. Nie widać tutaj zmiany o rząd wielkości, która mogłaby sama z siebie tłumaczyć przewagę N+1 nad Projection.

**Working Set nie jest wielkością alokacji**, a liczba GC Gen0 nie wyraża wprost kosztu GC przypisanego do danego endpointu. Mierzymy serwer ASP.NET Core, czyli również obsługę HTTP, serializację, biblioteki i pracę runtime.

Aby udowodnić, że konkretny odcinek czasu został zużyty przez GC lub JIT, potrzebowałbym analizy zdarzeń i stosów w odpowiednim przedziale czasu, nie tylko sum z licznika.

## Pułapka eksperymentu: poprawny plik śladu nie znaczy pełny ślad

Przy budowaniu automatyzacji pojawił się problem, który sam w sobie jest dobrym przykładem pracy diagnostycznej.

W serii `3b971dd5` użyłem początkowo limitu:

```text
dotnet-trace --duration 150s
```

Tymczasem komplet żądań zajmował około **168–170 sekund**. Narzędzie poprawnie zapisało plik `.nettrace`, ale przestało zbierać dane **zanim zakończył się cały workload**.

Co z tego wynika?

Nie mogę przypisać całej historii 80 żądań do śladu, który dokumentuje tylko jej część. Nie mogę też twierdzić, że większy rozmiar śladu Composite R2R — około **157 MB** w historycznej serii — dowodzi większego CPU, pamięci lub kosztu GC. Wielkość pliku zależy również od liczby i rodzaju zapisanych zdarzeń.

Poprawiłem więc skrypt: zbieranie `dotnet-trace` trwa do końca serii, a następnie otrzymuje **Enter przez pseudo-terminal i FIFO**. `dotnet-counters` kończy się analogicznie po wysłaniu `q`. Rozwiązanie wymagało też wymuszenia zakończeń linii **LF** dla skryptu Bash budowanego z repozytorium na Windows.

**Nowy mechanizm przeszedł test integracyjny na Docker Desktop (seria `b8e2a335`):**

- `PASS jit counters` — zapisano CSV o rozmiarze **266 456 bajtów**;
- `PASS jit trace` — zapisano ślad `.nettrace` o rozmiarze **26 108 814 bajtów**;
- wszystkie cztery strategie przeszły test zgodności danych.

Ten test **potwierdza poprawne zakończenie i zapis nowej sesji po workloadzie**. Nie przedstawiam go jeszcze jako niezależnej analizy osi czasu wszystkich zdarzeń wewnątrz pliku.

## Dlaczego nie wolno odejmować czasu SQL od czasu EF Core?

Powrócę do wyników z pierwotnej serii Query Store:

| Strategia | Mediana operacji EF, ms | Średni SQL CPU na żądanie, ms | Logical reads na żądanie |
|---|---:|---:|---:|
| N+1 | 119,83 | 21,40 | 1103 |
| Include | 6,01 | 1,95 | 14 |
| Projection | **5,11** | 2,73 | **14** |
| SplitQuery | 5,23 | **1,70** | 17 |

Może kusić, żeby od mediany 119,83 ms odjąć 21,40 ms i uzyskany wynik nazwać „narzutem EF Core”. To byłby błąd metodologiczny.

Po pierwsze, **mediana** operacji i **średni CPU SQL** nie są zgodnymi wielkościami statystycznymi. Po drugie, CPU silnika nie jest czasem oczekiwania klienta na wynik SQL. Po trzecie, w aplikacji występują także materializacja, oczekiwania, round-tripy, harmonogramowanie i budowa DTO.

Dlatego właśnie potrzebowałem **trzech perspektyw**:

1. `Stopwatch` w API — ile trwa dana operacja;
2. **Query Store** — jaką pracę wykonują instrukcje w SQL Server;
3. **EventPipe i liczniki CLR** — co robi cały proces aplikacji podczas workloadu.

Żadna z nich osobno nie wyjaśnia całego systemu.

## Jak powtórzyć profilowanie?

Laboratorium jest dostępne w repozytorium [WWSI_CSharp, demonstracja 67](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).

Po skonfigurowaniu `.env` i uruchomieniu laboratoryjnego SQL Server przejdź do katalogu demonstracji:

```powershell
git clone https://github.com/marcinpytlik/WWSI_CSharp.git
cd WWSI_CSharp/demonstracje/67_EfCorePerformanceLab

Copy-Item env.template .env
# W .env ustaw własne silne hasło SQL_SA_PASSWORD.

docker compose up -d sql

./experiments/03_Compilation/Run-EventPipeDiagnostics.ps1 `
    -Modes jit `
    -Take 100 `
    -Repetitions 10 `
    -CaptureSeconds 300
```

Aby uruchomić wszystkie tryby:

```powershell
./experiments/03_Compilation/Run-EventPipeDiagnostics.ps1 `
    -Modes jit,r2r,composite,no-tiering `
    -Take 100 `
    -Repetitions 20 `
    -CaptureSeconds 300
```

Wyniki trafiają do `experiments/03_Compilation/results/`: CSV liczników, CSV poszczególnych żądań, pliki `.nettrace`, logi i manifesty.

Parametr `CaptureSeconds` jest teraz **doradczy**: po jego przekroczeniu skrypt zgłosi ostrzeżenie, ale nie przerwie zbierania danych przed zakończeniem serii żądań.

**Nie stosuj tej konfiguracji na produkcyjnym SQL Server.** W demonstracji korzystamy z lokalnych kontenerów, syntetycznych danych, uproszczonego konta `sa` i wspólnej przestrzeni diagnostycznej.

## Wnioski: najpierw zapytania, potem kompilator

Po tych eksperymentach zabieram pięć obserwacji.

**Po pierwsze:** problem N+1 pozostaje dominujący niezależnie od badanej konfiguracji runtime. Kompilator nie zamienia 101 poleceń SQL w jedno.

**Po drugie:** Projection, Include i SplitQuery osiągają podobny rząd wielkości czasu przy tym wolumenie danych, ale różnią się kształtem SQL, liczbą round-tripów i kosztami po stronie silnika.

**Po trzecie:** niższa aktywność JIT nie gwarantuje niższej latencji. Trzeba rozróżnić koszt kompilacji i wydajność wykonywania już skompilowanego kodu.

**Po czwarte:** liczniki procesu i Query Store mają różnych „właścicieli”. Nie przypisuję sum alokacji całego API do pojedynczej operacji EF Core ani CPU SQL do czasu odpowiedzi HTTP.

**Po piąte:** sam fakt, że profiler zapisał plik, nie wystarcza. Trzeba jeszcze sprawdzić, czy obejmuje **cały badany przedział**.

W poprzednim artykule pytałem, czy sposób kompilacji potrafi istotnie wpłynąć na czas tej samej operacji. Odpowiedź po kolejnych pomiarach brzmi: **wpływ może występować, ale w naszym laboratorium nie zbliżył się do skali konsekwencji wyboru N+1**. Nie mam natomiast podstaw, żeby ogłosić jeden tryb kompilacji uniwersalnie najszybszym.

**Gdy optymalizujemy EF Core, pierwsze pytanie DBA nie powinno brzmieć „jak działa JIT?”, lecz „ile zapytań SQL naprawdę generuje ta operacja i co pokazuje Query Store?”.**

---

*Seria 03D: `3b971dd5`, 22 listopada 2026 r., 640 pomiarów operacji podczas profilowania. Poprawka zakończenia EventPipe zweryfikowana osobno w serii `b8e2a335`. Wcześniejsze pomiary Query Store: 10 powtórzeń na strategię, seria `fb6e09ce`. Wyniki dotyczą lokalnego stanowiska laboratoryjnego i nie stanowią uniwersalnego benchmarku EF Core, SQL Server ani sposobów kompilacji .NET. Surowe ślady nie były analizowane pod kątem stosów i osi czasu zdarzeń. Kod i pełny raport: [Demo 67](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).*
