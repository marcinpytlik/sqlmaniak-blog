---
title: ".NET 10, EF Core 10 i SQL Server 2022: JIT, ReadyToRun i Native AOT w 420 pomiarach"
date: 2026-11-08T08:00:00+01:00
slug: "dotnet10-efcore10-sqlserver-startup-jit-r2r-native-aot"
description: "Siedem wariantów kompilacji, dwa eksperymenty i 420 poprawnych pomiarów uruchomienia aplikacji .NET 10 z EF Core 10 i SQL Server 2022."
category: "SQL Server"
tags:
  - SQL Server
  - .NET 10
  - EF Core
  - Native AOT
  - ReadyToRun
  - benchmark
draft: false
---

# .NET 10, EF Core 10 i SQL Server 2022: JIT, ReadyToRun i Native AOT w 420 pomiarach

Ile naprawdę kosztuje uruchomienie niewielkiej aplikacji .NET, która tworzy kontekst Entity Framework Core, otwiera połączenie z SQL Server i wykonuje jedno zapytanie?

Z punktu widzenia administratora baz danych łatwo skupić się na czasie wykonania SQL. Ale zanim SQL Server otrzyma zapytanie, po stronie klienta musi wydarzyć się sporo: uruchomienie procesu, inicjalizacja środowiska, załadowanie bibliotek, przygotowanie EF Core i otwarcie połączenia.

Postanowiłem to zmierzyć. Przygotowałem **siedem wariantów publikacji** aplikacji .NET 10 i przeprowadziłem **dwa eksperymenty po 210 uruchomień**. Wszystkie 420 pomiarów zakończyło się sukcesem.

> **Najważniejsze zastrzeżenie:** to benchmark krótkotrwałego procesu aplikacyjnego, a nie test wydajności silnika SQL Server ani ogólny ranking przepustowości aplikacji .NET.

## Środowisko i zakres

| Element | Konfiguracja |
|---|---|
| System hosta | Windows 11, build 26300 |
| .NET | 10.0.14 |
| EF Core | 10.0.14 |
| SQL Server | SQL Server 2022 w Dockerze |
| Endpoint SQL | 127.0.0.1:14333 |
| PowerShell (drugi eksperyment) | 7.6.9 |
| Liczba wariantów | 7 |
| Liczba poprawnych pomiarów | 420 |

Nie mam w komplecie danych pomiarowych pełnej specyfikacji CPU/RAM hosta ani identyfikatora obrazu SQL Server. To ogranicza możliwość dokładnego odtworzenia wyników na innym komputerze.

Każdy proces wykonuje tę samą sekwencję: tworzy `DbContextOptions` i `LabDbContext`, otwiera połączenie, wykonuje `SELECT 1` przez `ExecuteSqlRawAsync`, zapisuje wynik JSON i kończy działanie.

```csharp
var create = Stopwatch.StartNew();
var options = new DbContextOptionsBuilder<LabDbContext>()
    .UseSqlServer(connectionString)
    .Options;
await using var db = new LabDbContext(options);
create.Stop();

var open = Stopwatch.StartNew();
await db.Database.OpenConnectionAsync();
open.Stop();

var query = Stopwatch.StartNew();
var affected = await db.Database.ExecuteSqlRawAsync("SELECT 1");
query.Stop();
```

To nie jest test LINQ ani kompilacji zapytań LINQ. `SELECT 1` nie służy tu do mierzenia szybkości przetwarzania danych przez SQL Server. `ExecuteSqlRawAsync` dla tego zapytania zwracał `-1` jako wynik liczby zmodyfikowanych wierszy — nie jest to błąd.

## Co mierzyłem?

- **WallMs** — czas całego procesu, mierzony zewnętrznym skryptem od uruchomienia do zakończenia.
- **ContextMs** — konfiguracja i utworzenie kontekstu EF Core.
- **ConnectionMs** — pierwsze `OpenConnectionAsync`.
- **SqlMs** — wywołanie `ExecuteSqlRawAsync("SELECT 1")`, łącznie z kosztami po stronie klienta.
- **ManagedTotalMs** — czas od pierwszej instrukcji zarządzanej do zakończenia operacji SQL, **przed** serializacją wyniku.
- **WorkingSetBytes** — pamięć procesu w chwili pomiaru, nie szczyt użycia pamięci.

Nie należy dodawać osobnych median etapów i oczekiwać dokładnie mediany całości: mediany są liczone niezależnie.

## Siedem wariantów

| Oznaczenie | Publikacja |
|---|---|
| B1-JIT | `PublishReadyToRun=false` |
| R1-R2R | `PublishReadyToRun=true` |
| R2-Composite | `PublishReadyToRun=true`, `PublishReadyToRunComposite=true` |
| R3-NoTiering | `PublishReadyToRun=true`, `TieredCompilation=false` |
| A1-AOT | `PublishAot=true` |
| A2-AOT-Size | `PublishAot=true`, `OptimizationPreference=Size` |
| A3-AOT-Speed | `PublishAot=true`, `OptimizationPreference=Speed` |

ReadyToRun zawiera kod natywny przygotowany wcześniej, ale nadal korzysta ze środowiska .NET i może współpracować z JIT. Native AOT kompiluje aplikację natywnie na etapie publikacji. Wyłączenie Tiered Compilation nie jest nową techniką kompilacji — to odrębna konfiguracja działania runtime.

## Benchmark 1: Sequential

Najpierw uruchomiłem każdy wariant **30 razy z rzędu**. Wszystkie 210 prób zakończyły się poprawnie.

| Wariant | Mediana WallMs | P95 WallMs |
|---|---:|---:|
| B1-JIT | 932,77 ms | 1091,90 ms |
| R1-R2R | 533,71 ms | 646,69 ms |
| R2-Composite | 435,29 ms | 506,52 ms |
| R3-NoTiering | 632,99 ms | 752,96 ms |
| A1-AOT | 123,52 ms | 229,70 ms |
| A2-AOT-Size | 130,06 ms | 199,22 ms |
| A3-AOT-Speed | **121,85 ms** | 167,28 ms |

Native AOT osiągnął wyraźnie krótszy czas całego procesu. Ale czy kolejność testów nie wpłynęła na wynik? Po 30 kolejnych uruchomieniach jednego wariantu cache systemu i stan środowiska mogą być inne niż podczas testowania następnego.

Dlatego przeprowadziłem drugi eksperyment.

## Benchmark 2: Interleaved

Tym razem wykonałem **30 rund**, a w każdej rundzie wszystkie siedem wariantów uruchamiałem w kolejności losowanej algorytmem Fishera–Yatesa. Dwie rundy rozgrzewkowe nie zostały wliczone do wyników.

Parametry drugiej serii: `Rounds=30`, `WarmupRounds=2`, `Seed=20261107`, timeout pojedynczego procesu 60 sekund. Percentyl P95 wyznaczałem interpolacją liniową przy pozycji `(n-1)*p`.

Znów **210/210 prób zakończyło się sukcesem**.

![Porównanie median WallMs w obu eksperymentach](/images/dotnet10-startup-wall-2026.svg)

| Wariant | Mediana WallMs | P95 WallMs | Mediana ManagedTotalMs |
|---|---:|---:|---:|
| B1-JIT | 930,47 ms | 1072,11 ms | 748,68 ms |
| R1-R2R | 540,78 ms | 588,75 ms | 374,12 ms |
| R2-Composite | 448,21 ms | 487,21 ms | 274,11 ms |
| R3-NoTiering | 642,79 ms | 723,48 ms | 462,25 ms |
| A1-AOT | 134,43 ms | 147,48 ms | 82,84 ms |
| A2-AOT-Size | 142,03 ms | 182,37 ms | 80,70 ms |
| A3-AOT-Speed | **131,49 ms** | 141,56 ms | 80,44 ms |

Ranking wariantów nie zmienił się. W drugiej serii mediana A3-AOT-Speed była o **85,9% niższa** niż mediana B1-JIT — około **7,1 razy krótszy czas procesu**.

To mocna obserwacja w ramach badanego scenariusza. Nie oznacza, że każda aplikacja Native AOT będzie siedem razy szybsza.

Różnica między medianami A1-AOT i A3-AOT-Speed wyniosła zaledwie **2,94 ms**. Nie traktuję jej jako dowodu przewagi optymalizacji `Speed` bez dodatkowych eksperymentów.

## Gdzie znika czas?

Poniżej mediany etapów z drugiego eksperymentu:

| Etap | JIT | Composite R2R | AOT Speed |
|---|---:|---:|---:|
| ContextMs | 187,42 ms | 81,40 ms | 18,10 ms |
| ConnectionMs | 502,35 ms | 180,62 ms | 59,80 ms |
| SqlMs | 56,79 ms | 10,50 ms | 2,28 ms |

Największa różnica nie dotyczy samego zapytania. Widać ją również podczas inicjalizacji kontekstu i pierwszego otwarcia połączenia.

**Uwaga DBA:** `SqlMs` nie jest pomiarem czasu pracy silnika SQL Server. Obejmuje także koszty klienta, EF Core, SqlClient i komunikacji. Na podstawie tych liczb nie wolno twierdzić, że SQL Server wykonuje `SELECT 1` kilkadziesiąt razy szybciej.

## Pamięć procesu

![Mediana Working Set według wariantu](/images/dotnet10-startup-memory-2026.svg)

| Wariant | Mediana Working Set |
|---|---:|
| B1-JIT | 56,71 MiB |
| R1-R2R | 55,13 MiB |
| R2-Composite | 57,11 MiB |
| R3-NoTiering | 55,82 MiB |
| A1-AOT | 26,83 MiB |
| A2-AOT-Size | 36,40 MiB |
| A3-AOT-Speed | 26,82 MiB |

W tym eksperymencie A1 i A3 miały niższy Working Set niż warianty korzystające z runtime .NET. Ciekawy jest A2-AOT-Size: optymalizacja rozmiaru binariów **nie oznacza automatycznie** najmniejszego Working Set.

Nie zestawiam tutaj rozmiarów plików publikacji, ponieważ nie zebrałem jeszcze ich zweryfikowanych wartości. Working Set nie jest też pomiarem maksymalnego zużycia pamięci.

## Droga do działającego Native AOT: dwa rzeczywiste problemy

### 1. EF Core wymagał skompilowanego modelu

Pierwsze publikacje Native AOT kończyły się przy uruchomieniu komunikatem:

```text
Model building is not supported when publishing
with NativeAOT. Use a compiled model.
```

Dodałem `Microsoft.EntityFrameworkCore.Design`, przygotowałem fabrykę `IDesignTimeDbContextFactory<LabDbContext>` i wygenerowałem model:

```powershell
dotnet ef dbcontext optimize `
    --project .\src\StartupLab\StartupLab.csproj `
    --startup-project .\src\StartupLab\StartupLab.csproj `
    --output-dir CompiledModels `
    --namespace StartupLab.CompiledModels `
    --nativeaot
```

Powstały pliki `LabDbContextAssemblyAttributes.cs`, `LabDbContextModel.cs` i `LabDbContextModelBuilder.cs`. Narzędzie poinformowało, że model będzie wykrywany automatycznie. Po zmianie modelu trzeba go wygenerować ponownie.

### 2. JSON wymagał Source Generation

Następny błąd był związany z serializacją anonimowego obiektu:

```text
Reflection-based serialization has been disabled
for this application.
```

Zastąpiłem obiekt anonimowy jawnym typem `BenchmarkResult` i dodałem kontekst `System.Text.Json`:

```csharp
[JsonSourceGenerationOptions(
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase)]
[JsonSerializable(typeof(BenchmarkResult))]
internal partial class BenchmarkJsonContext : JsonSerializerContext
{
}
```

Wszystkie warianty zachowały identyczny kontrakt JSON wykorzystywany przez skrypt pomiarowy.

Publikacja AOT nadal generowała ostrzeżenia związane z trimmingiem i zgodnością EF Core oraz SqlClient. **Udane uruchomienie testu nie dowodzi pełnej zgodności biblioteki ze wszystkimi scenariuszami Native AOT.**

## Poboczny problem: Windows Code Integrity

Podczas przygotowywania wariantów ReadyToRun system Windows blokował wybrane artefakty zgodnie z polityką `VerifiedAndReputableDesktop`. Pierwotny wariant R3 zakończył się kodem `0xC0000602`.

Kontrolowany eksperyment wykazał jednak, że świeży R3 działa zarówno bez podpisu, jak i po podpisaniu DLL. Nie potwierdziłem więc, aby samo podpisanie było przyczyną awarii pierwotnego pliku.

To istotna lekcja metodologiczna: **najpierw weryfikujemy, że każdy wariant wykonuje tę samą operację, dopiero później interpretujemy wyniki wydajności.**

## Czego ten benchmark nie dowodzi?

Nie badałem przepustowości długotrwale działającej aplikacji, ASP.NET Core, dużych zapytań LINQ, materializacji wyników, change trackingu ani obciążenia wielowątkowego.

Drugi eksperyment ogranicza wpływ kolejności uruchamiania, ale nie usuwa wpływu planisty Windows, cache, stanu kontenera SQL Server i innych czynników. Nie przeprowadzałem formalnego testu istotności różnic pomiędzy A1 i A3.

Co ważne, w tej serii wszystkie warianty korzystały już ze wspólnego kodu z wygenerowanym modelem EF Core i JSON Source Generation. Porównujemy **konfiguracje publikacji i uruchomienia tej samej aplikacji**, a nie izolowaną wydajność samego kompilatora.

## Wnioski

1. **Native AOT zdecydowanie skrócił czas całego procesu** w badanym scenariuszu: około 131,49 ms mediany dla A3 wobec 930,47 ms dla JIT w drugim eksperymencie.
2. **Composite ReadyToRun był najszybszy spośród wariantów bez Native AOT**, z medianą 448,21 ms.
3. **Przeplatanie wariantów nie zmieniło ich rankingu**, co zwiększa zaufanie do obserwowanego trendu.
4. **Znaczna część różnicy występuje przed i wokół pierwszego wywołania SQL**, nie w samym silniku bazy danych.
5. **Native AOT wymaga pracy nad zgodnością** — w tym eksperymencie skompilowanego modelu EF Core i serializacji JSON bez refleksji.

Dla krótkotrwałych narzędzi CLI, procesów uruchamianych na żądanie czy zadań wykonywanych cyklicznie koszt startu może mieć duże znaczenie. W usługach pracujących nieprzerwanie przez wiele godzin wynik może wyglądać inaczej.

**Najważniejszy wniosek z perspektywy DBA: wydajność operacji korzystającej z SQL Server zaczyna się jeszcze zanim serwer otrzyma pierwsze zapytanie.**

---

*Eksperyment: 7 wariantów × 30 prób × 2 serie = 420 poprawnych pomiarów. Wyniki pochodzą z plików `summary-20261107-194308.csv` oraz `summary-interleaved-20261107-195140.csv`. Kolejnym naturalnym krokiem będzie odtworzenie eksperymentu w kontenerach Linux i Kubernetes — ale to temat na osobny artykuł.*
