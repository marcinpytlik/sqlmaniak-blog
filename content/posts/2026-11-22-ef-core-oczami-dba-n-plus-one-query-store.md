---
title: "EF Core oczami DBA: 101 zapytań kontra jedno. Co naprawdę pokazuje Query Store?"
date: 2026-11-22T12:00:00+01:00
slug: "ef-core-n-plus-one-include-projection-split-query-query-store"
description: "Kontrolowany eksperyment .NET 10, EF Core 10 i SQL Server 2022: N+1, Include, Projection i SplitQuery. Prawdziwe pomiary czasu, CPU i logical reads oraz pytanie o JIT i AOT."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - EF Core
  - .NET 10
  - Query Store
  - N+1
  - performance tuning
  - ORM
draft: true
---

# EF Core oczami DBA: 101 zapytań kontra jedno. Co naprawdę pokazuje Query Store?

**Czy problem N+1 to wyłącznie kwestia liczby poleceń SQL? A jeśli projekcja DTO jest najszybsza z perspektywy aplikacji, to czy koniecznie zużywa najmniej CPU po stronie SQL Server?**

Zamiast odpowiadać intuicyjnie, zbudowałem powtarzalne laboratorium na **.NET 10, EF Core 10 i SQL Server 2022**. Wykonałem cztery warianty tego samego odczytu, zmierzyłem ich czas w aplikacji, a następnie porównałem przyrosty liczników w Query Store.

Wyniki pokazują dwie rzeczy: koszt N+1 jest bardzo konkretny, ale **najkrótszy czas aplikacji nie musi oznaczać najtańszego zapytania dla silnika bazy danych**.

Kod, kontenery i gotowe skrypty dla czytelników:

**[WWSI_CSharp — demonstracja 67: EF Core Performance Lab](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab)**

## Środowisko laboratoryjne i zakres porównania

Wyniki należy zawsze odczytywać w kontekście konkretnego stanowiska. W [poprzednim artykule o JIT, ReadyToRun i Native AOT](https://sqlmaniak.blog/posts/dotnet10-efcore10-sqlserver-startup-jit-r2r-native-aot/) udokumentowałem następującą konfigurację sprzętową i programową:

| Element | Konfiguracja stanowiska opisana we wcześniejszym laboratorium |
|---|---|
| System hosta | Microsoft Windows 11 Pro, wersja 10.0.26300 (build 26300), x64 |
| Procesor | Intel Core i5-1035G1 @ 1,00 GHz |
| Rdzenie fizyczne / procesory logiczne | 4 / 8 |
| Pamięć RAM hosta | 7,81 GiB |
| .NET SDK | 10.0.403 |
| .NET / EF Core (w poprzednim teście) | 10.0.14 / 10.0.14 |
| PowerShell (w poprzednim teście) | 7.6.9 |
| Docker Client / Engine (w poprzednim teście) | 29.9.2 / 29.9.2 |
| Środowisko kontenerów (w poprzednim teście) | Linux, 8 CPU; ok. 3,73 GiB pamięci raportowane przez `docker info` |

**Oba eksperymenty przeprowadziłem na tym samym komputerze, z tym samym procesorem, pamięcią RAM i systemem operacyjnym.** Konfigurację sprzętową potwierdziłem dla obu laboratoriów. Wersje narzędzi i zasoby poszczególnych kontenerów są jednak parametrami osobnymi — nie zakładam bez nowego odczytu, że pozostały identyczne.

Dla **EF Core Performance Lab 67** konfiguracja odtwarzalna z [repozytorium demonstracji](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab) jest następująca:

| Element | Konfiguracja demonstracji 67 |
|---|---|
| Aplikacja | ASP.NET Core / .NET 10, EF Core 10, API budowane w Dockerze |
| Silnik bazy | SQL Server 2022 Developer, kontener Linux |
| Obraz SQL Server | `mcr.microsoft.com/mssql/server:2022-latest` |
| Endpoint SQL na hoście | `127.0.0.1:14367` |
| Endpoint API na hoście | `127.0.0.1:5087` |
| Baza danych | `EfPerformanceLab` |
| Dane testowe | 100 zamówień i 1000 pozycji (10 pozycji na zamówienie) |
| Query Store | `READ_WRITE`, `QUERY_CAPTURE_MODE = ALL` |
| Próba | 10 wywołań każdej z 4 strategii, osobne snapshoty BEFORE/AFTER |
| Identyfikator serii | `fb6e09ce`, 22 listopada 2026 r. |

W poprzednim eksperymencie SQL Server działał w **innym kontenerze**, `sql2022-startuplab`, na porcie **14333**. Tam potwierdziłem wersję **SQL Server 2022 RTM-CU27, 16.0.4295.3**, a także limit pamięci kontenera **4 GiB**. **Nie przenoszę tych dwóch parametrów automatycznie na demonstrację 67** — jej obraz z tagiem `2022-latest` może wskazywać inną wersję silnika, a plik Compose demonstracji 67 nie deklaruje limitu pamięci SQL Server.

Dla pełnej reprodukowalności kolejnych pomiarów mogę zapisać rzeczywiste parametry pracującego kontenera demonstracji 67:

```powershell
docker compose exec -T sql bash -c 'export SQLCMDPASSWORD="$MSSQL_SA_PASSWORD"; /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -d master -h -1 -W -Q "SET NOCOUNT ON; SELECT @@VERSION;"'
docker compose ps
docker version
docker info
```

To samo stanowisko sprzętowe ułatwia zestawienie obu eksperymentów, choć konfigurację kontenera SQL należy dokumentować oddzielnie.

## Jedne dane, cztery strategie

Środowisko demonstracyjne zawiera 100 zamówień, z których każde ma 10 pozycji: **100 rekordów Orders i 1000 rekordów OrderItems**. Każda strategia zwraca tę samą strukturę DTO, identyczny zestaw rekordów i kolejność elementów.

| Wariant | Mechanizm | Liczba poleceń SQL na żądanie |
|---|---|---:|
| **N+1** | Jeden SELECT zamówień, następnie SELECT pozycji w pętli | **101** |
| **Include** | `Include(x => x.Items)` + `AsSingleQuery()` | **1** |
| **Projection** | `Select()` bezpośrednio do DTO + `AsSingleQuery()` | **1** |
| **SplitQuery** | `Include(x => x.Items)` + `AsSplitQuery()` | **2** |

We wszystkich wariantach stosuję `AsNoTracking()`. N+1 implementuję jawnie, bez lazy-loading proxies. Chodzi o obserwację skutku: jeden odczyt rodziców i osobny odczyt dzieci dla każdego rodzica.

Uproszczony przykład antywzorca:

```csharp
var orders = await db.Orders
    .AsNoTracking()
    .OrderBy(o => o.Id)
    .Take(100)
    .ToListAsync();

foreach (var order in orders)
{
    var items = await db.OrderItems
        .AsNoTracking()
        .Where(i => i.OrderId == order.Id)
        .ToListAsync();

    // Zbudowanie DTO zamówienia i jego pozycji.
}
```

**To nie jest propozycja implementacji produkcyjnej.** To celowo nieefektywny wzorzec służący do pomiaru.

Dla porównania `Include` pobiera powiązane dane w pojedynczym zapytaniu:

```csharp
var orders = await db.Orders
    .AsNoTracking()
    .AsSingleQuery()
    .OrderBy(o => o.Id)
    .Take(100)
    .Include(o => o.Items)
    .ToListAsync();
```

Wariant projekcji wybiera dane bezpośrednio do DTO, a `AsSplitQuery()` dzieli odczyt rodziców i jednej kolekcji na dwa polecenia SQL. W rzeczywistym kodzie wszystkie warianty konwertują wynik do **identycznego kontraktu odpowiedzi**.

## Jak mierzyłem, żeby nie porównywać przypadkowych liczb?

Najpierw sprawdziłem poprawność danych i liczbę wykonywanych poleceń za pomocą `DbCommandInterceptor`. Dopiero potem rozpocząłem pomiary.

W końcowej serii automatycznej zastosowałem:

- **10 powtórzeń na wariant**, czyli 40 pomiarów operacji EF Core;
- warm-up przed właściwymi seriami;
- osobne serie dla N+1, Include, Projection i SplitQuery;
- dla każdej serii snapshot Query Store **BEFORE**, benchmark, snapshot **AFTER**;
- kontrolę, czy Query Store zanotował oczekiwaną liczbę wykonań poleceń.

To ostatnie ma znaczenie. Wcześniejsze odczyty z Query Store pokazywały na przykład 4271 wykonań instrukcji pobierającej pozycje, ale nie odpowiadały jednemu kontrolowanemu przedziałowi benchmarku. Takiej historycznej sumy **nie wolno** mechanicznie porównywać z dziesięcioma wywołaniami innego endpointu.

Podczas przygotowywania snapshotów stwierdziłem, że w tym środowisku tekst zapytań udostępniany przez Query Store nie pozwalał mi wiarygodnie filtrować instrukcji po komentarzach `TagWith()`. Pierwotne filtrowanie po znaczniku `EFPLAB:` zwracało zero trafień przed testem i jedno po nim — przy czym dopasowywało samo zapytanie diagnostyczne zawierające ten znacznik jako literał. Nie ustaliłem, z jakiego powodu komentarze nie były dostępne w oczekiwanej postaci. Zamiast zakładać ich obecność, rozpoznawałem charakterystyczne fragmenty SQL i wykonywałem pomiary każdej strategii osobno.

To dobre przypomnienie dla DBA: **zanim porównasz liczby z narzędzia diagnostycznego, upewnij się, że rzeczywiście mierzysz te same zakresy pracy**.

## Wyniki EF Core: 119,83 ms kontra 5,11 ms

W kontrolowanym przebiegu uzyskałem następujące mediany czasu operacji po stronie aplikacji:

| Strategia | Mediana czasu EF Core | Polecenia SQL |
|---|---:|---:|
| N+1 | **119,83 ms** | 101 |
| Include | **6,01 ms** | 1 |
| Projection | **5,11 ms** | 1 |
| SplitQuery | **5,23 ms** | 2 |

W tej konkretnej serii:

- Include osiągnął medianę około **19,9 razy krótszą** od N+1;
- Projection — około **23,5 razy krótszą**;
- SplitQuery — około **22,9 razy krótszą**.

Czy zatem Projection jest zawsze najlepszym wyborem? **Nie.** Różnice między trzema szybszymi wariantami są niewielkie; do ich wiarygodnej oceny potrzebowałbym większej próby, różnych wolumenów danych i analizy planów wykonania.

Co ważne, `Stopwatch` mierzył czas od rozpoczęcia operacji EF Core do przygotowania obiektów wynikowych. Nie obejmował całej transmisji HTTP ani serializacji JSON.

## Query Store: co widzi SQL Server?

Tutaj pojawia się najciekawszy fragment eksperymentu.

Średnie koszty silnika SQL Server, przeliczone z przyrostów Query Store **na jedno żądanie**, wyniosły:

| Strategia | CPU SQL / żądanie | Suma duration SQL / żądanie | Logical reads / żądanie |
|---|---:|---:|---:|
| N+1 | **21,40 ms** | 21,43 ms | **1103** |
| Include | **1,95 ms** | 1,95 ms | **14** |
| Projection | **2,73 ms** | 2,73 ms | **14** |
| SplitQuery | **1,70 ms** | 1,70 ms | **17** |

Przy N+1 otrzymałem **1103 logical reads**, a przy Include i Projection — po **14**. Oznacza to redukcję odczytów logicznych o około **98,7%**.

Wcześniejsza, niezależna seria N+1 również pokazała dokładny przyrost: **1000 wykonań SELECT na OrderItems i 10 wykonań SELECT na Orders**. Odpowiadały one łącznie **11 030 logical reads** dla dziesięciu żądań, czyli także 1103 na żądanie.

Nie są to fizyczne odczyty z dysku. Logical reads oznaczają odczyty stron wewnątrz silnika SQL Server, również wtedy, gdy strony znajdują się już w buffer pool.

### 101 tanich zapytań może być droższe niż jedno większe

W pojedynczym wykonaniu zapytanie pobierające pozycje zamówienia kosztuje niewiele. Jednak N+1 powiela ten koszt oraz liczbę operacji między aplikacją a SQL Server.

Różnica nie sprowadza się do tego, że pojedynczy SELECT z JOIN jest zawsze szybszy od SELECT po kluczu obcym. Problemem jest **sumaryczny koszt całej operacji biznesowej**, a nie koszt pojedynczej instrukcji oglądanej bez kontekstu.

Dla DBA to ważna zmiana perspektywy. Zapytanie o bardzo niskim średnim duration może być poważnym problemem, jeżeli wykonywane jest setki tysięcy razy.

## Paradoks: najkrótszy czas EF, ale nie najmniejszy CPU SQL

Przyjrzałem się również trzem szybszym wariantom:

| Metryka | Include | Projection | SplitQuery |
|---|---:|---:|---:|
| Mediana EF Core | 6,01 ms | **5,11 ms** | 5,23 ms |
| CPU SQL | 1,95 ms | 2,73 ms | **1,70 ms** |
| Logical reads | **14** | **14** | 17 |
| Polecenia SQL | **1** | **1** | 2 |

**Projection miał najkrótszą medianę czasu w aplikacji, ale największy średni CPU SQL spośród tej trójki.** Z kolei SplitQuery miał najniższy średni CPU SQL, lecz wykonał dwa polecenia i więcej logical reads.

To nie jest sprzeczność. W eksperymencie mierzyłem różne składowe operacji:

- SQL Server wykonuje plan i zwraca wiersze;
- EF Core materializuje wynik albo tworzy DTO;
- aplikacja przygotowuje strukturę odpowiedzi;
- liczba round-tripów wpływa na czas, ale nie jest tożsama z CPU silnika.

Do tego porównuję **medianę czasu aplikacji** ze **średnim CPU SQL na żądanie**. Nie wolno po prostu odjąć 2,73 ms CPU od 5,11 ms czasu i nazwać różnicy „narzutem EF Core”.

SplitQuery okazał się konkurencyjny. Nie jest to jednak argument za domyślnym używaniem `AsSplitQuery()`: przy wielu kolekcjach może ograniczyć mnożenie wierszy przez JOIN-y, ale wymaga dodatkowych poleceń SQL.

## Jak odtworzyć cały eksperyment?

Kod źródłowy, pliki Docker, SQL oraz instrukcja dla studentów są publicznie dostępne:

[**EF Core Performance Lab 67 — kompletna demonstracja**](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab)

Wymagania: Docker Desktop, PowerShell 7, Git. Lokalny .NET SDK i SSMS nie są obowiązkowe.

```powershell
git clone https://github.com/marcinpytlik/WWSI_CSharp.git
cd WWSI_CSharp/demonstracje/67_EfCorePerformanceLab

Copy-Item env.template .env
# Ustaw własne silne hasło SQL_SA_PASSWORD w .env.

docker compose up -d --build
Invoke-RestMethod http://localhost:5087/health
```

Przed pełnym benchmarkiem ustaw w **laboratoryjnej** bazie Query Store w trybie `ALL` (po inicjalizacji API):

```sql
ALTER DATABASE EfPerformanceLab
SET QUERY_STORE (
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = ALL
);
```

Sprawdź poprawność, a następnie uruchom jedno polecenie do kompleksowego porównania:

```powershell
./scripts/Test-Lab.ps1 -Take 100

./scripts/Run-All-Benchmark.ps1 -Take 100 -Repetitions 10
```

Skrypt wykonuje cztery niezależne serie i wyświetla zbiorczą tabelę z czasem aplikacji, CPU SQL i logical reads. Zapisuje też dwa pliki CSV z identyfikatorem przebiegu, dzięki którym można przeanalizować dane szczegółowe.

**Nie wykonuj tego eksperymentu na produkcyjnej bazie.** Demonstracja wykorzystuje uproszczone uprawnienia `sa`, kontrolowany seed oraz automatyczne tworzenie schematu — wyłącznie na potrzeby lokalnego laboratorium. Szczegóły konfiguracji i rozwiązywania problemów znajdziesz w README.

## A co z JIT, ReadyToRun i Native AOT?

Kolejna sprawa — i pytanie, jakie przyszło mi na myśl po analizie wyników — dotyczy sposobu kompilacji aplikacji.

Jeżeli SQL Server zużywał średnio około 21,40 ms CPU dla N+1, a mediana operacji EF Core wyniosła 119,83 ms, to **co dzieje się poza silnikiem bazy?** Ile znaczą wykonanie kodu, materializacja obiektów, komunikacja z SQL, alokacje i GC?

Czy sposób kompilacji .NET może to zmienić?

Potrzebny będzie oddzielny eksperyment z tym samym modelem danych i tymi samymi zapytaniami, ale różnymi wariantami publikowania aplikacji:

1. CoreCLR z JIT;
2. ReadyToRun;
3. Composite ReadyToRun;
4. wariant z wyłączoną kompilacją warstwową;
5. Native AOT — jeżeli uda mi się zapewnić zgodność aplikacji z ograniczeniami tego trybu.

Native AOT nie jest jedynie przełącznikiem, który bezwarunkowo zadziała dla każdej konfiguracji EF Core. Nie wolno też utożsamiać poprawy czasu startu aplikacji z poprawą kosztu wykonania zapytania SQL.

**Na dziś nie mam jeszcze wyników benchmarku JIT vs AOT dla tej demonstracji.** Mam za to bardzo solidny punkt odniesienia, na którym mogę oprzeć kolejny eksperyment.

I już teraz jedna rzecz wydaje się pewna: zmiana sposobu kompilacji aplikacji sama w sobie nie sprawi, że 101 wywołań SQL magicznie zamieni się w jedno.

## Wnioski

Z tego laboratorium zabieram cztery praktyczne obserwacje:

1. **Optymalizuj całą operację biznesową, a nie tylko pojedynczy SELECT.** N+1 może generować tysiące odczytów i round-tripów przez pozornie tanie polecenia.
2. **Nie wybieraj strategii wyłącznie po medianie czasu EF Core.** Sprawdź również CPU, liczbę wykonań i logical reads w SQL Server.
3. **Prawidłowy pomiar jest równie ważny jak optymalizacja.** Snapshoty BEFORE/AFTER i kontrola liczby wykonań pozwalają uniknąć porównywania przypadkowych fragmentów historii Query Store.
4. **Nie szukaj jednej uniwersalnej recepty.** Projection, Include i SplitQuery mają odmienne kompromisy. Decyzję podejmuj na podstawie modelu, wolumenu danych i realnych pomiarów.

Na pytanie „który wariant wygrał?” odpowiedź brzmi: w moim scenariuszu Projection miał najkrótszą medianę EF Core, SplitQuery najniższe średnie CPU SQL, a N+1 — zdecydowanie najwyższy koszt.

Ale pytanie, które najbardziej mnie interesuje, pozostaje otwarte:

**Czy JIT, ReadyToRun albo Native AOT istotnie wpłyną na czas tej samej operacji, jeżeli SQL Server wykonuje dokładnie tę samą pracę?**

To temat kolejnej odsłony laboratorium.

---

*Wszystkie wyniki wydajnościowe dotyczą kontrolowanej serii `fb6e09ce` z 22 listopada 2026 r. w demonstracji 67. Oba eksperymenty wykonałem na tym samym komputerze; dokładna wersja CU i limit pamięci kontenera SQL w serii 67 nie zostały osobno udokumentowane. Nie jest to uniwersalny benchmark EF Core ani SQL Server. Kod i metodologia: [WWSI_CSharp](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).*
