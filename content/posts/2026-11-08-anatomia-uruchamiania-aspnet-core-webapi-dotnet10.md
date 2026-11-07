---
title: "Od dotnet new do pierwszego HTTP 200. Anatomia uruchamiania ASP.NET Core Web API w .NET 10"
date: 2026-11-08T10:00:00+01:00
slug: "anatomia-uruchamiania-aspnet-core-webapi-dotnet10"
description: "Co dzieje się między dotnet new, dotnet build i pierwszą odpowiedzią HTTP 200? CoreCLR, IL, JIT, Kestrel oraz wyniki 60 pomiarów na Windows x64."
category: ".NET"
tags:
  - .NET 10
  - ASP.NET Core
  - Web API
  - CoreCLR
  - JIT
  - Kestrel
  - performance
draft: false
---

# Od `dotnet new` do pierwszego HTTP 200. Anatomia uruchamiania ASP.NET Core Web API w .NET 10

Wykonujemy trzy polecenia:

```powershell
dotnet new webapi
dotnet build
dotnet run
```

Po chwili konsola pokazuje `Now listening on: http://127.0.0.1:5080`, a endpoint odpowiada HTTP 200. Co wydarzyło się pomiędzy tymi momentami? Czy `dotnet build` tworzy kod maszynowy? Kiedy działa JIT? Kto uruchamia serwer HTTP? I dlaczego czas mierzony wewnątrz aplikacji różni się od czasu do pierwszej odpowiedzi?

Sprawdziłem to na niewielkim Web API w .NET 10. Wykonałem **60 uruchomień** — po 30 w konfiguracjach Debug i Release — i zestawiłem pomiar wewnętrzny z zewnętrznym.

> To artykuł o mechanizmach uruchamiania aplikacji, poparty pomiarami konkretnego środowiska. Nie jest to uniwersalny ranking wydajności Debug i Release.

## Środowisko

| Element | Konfiguracja |
|---|---|
| System | Windows 11 Pro, build 26300, x64 |
| Procesor | Intel Core i5-1035G1, 4 rdzenie / 8 procesorów logicznych |
| RAM | 7,81 GiB |
| .NET SDK | 10.0.403 |
| .NET Runtime | 10.0.14 |
| PowerShell | 7.6.9 |
| Aplikacja | Minimal ASP.NET Core Web API, bez bazy danych |
| Liczba pomiarów | 30 Debug + 30 Release |

Brak bazy danych jest celowy: chcemy obserwować przede wszystkim start procesu, runtime i serwera HTTP, a nie koszt połączenia z SQL Server.

## 1. `dotnet new`: generowanie projektu

```powershell
mkdir C:\Lab\WebApiStartup
cd C:\Lab\WebApiStartup
dotnet new webapi -n StartupWebApi --framework net10.0 --no-https
cd StartupWebApi
```

Szablon tworzy m.in. `StartupWebApi.csproj`, `Program.cs`, konfigurację aplikacji oraz profil uruchamiania. Samo `dotnet new` nie jest kompilacją aplikacji.

Kluczowe ustawienia projektu:

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
</Project>
```

`Microsoft.NET.Sdk.Web` dostarcza mechanizmy budowania aplikacji ASP.NET Core, a `net10.0` wskazuje docelowy framework. Nie oznacza to jeszcze kompilacji całego programu do natywnego kodu x64.

## 2. `dotnet build`: od C# do IL

```powershell
dotnet build -c Debug
dotnet build -c Release
```

W standardowym wariancie kompilator Roslyn przekształca kod C# w **Common Intermediate Language (IL)** wraz z metadanymi. W katalogu `bin\Release\net10.0` znajdziemy m.in.:

- `StartupWebApi.dll` — zestaw z IL i metadanymi;
- `StartupWebApi.exe` — natywny host uruchamiający aplikację;
- `StartupWebApi.runtimeconfig.json` — informacje o środowisku uruchomieniowym;
- `StartupWebApi.deps.json` — opis zależności.

**Obecność pliku EXE nie oznacza Native AOT.** W zwykłym buildzie kod aplikacji nadal może być kompilowany przez JIT podczas wykonania.

![Od kodu C# przez Roslyn i IL do kodu maszynowego x64](/images/webapi-dotnet10-kompilacja-il-jit.svg)

Schemat jest uproszczony: część bibliotek platformy może korzystać z kodu przygotowanego wcześniej, np. ReadyToRun. JIT nie musi kompilować wszystkich metod przy starcie.

## 3. Minimalne Web API

Na potrzeby eksperymentu użyłem trzech endpointów: `/ping`, `/runtime` i `/work`. Pierwszy służy do wykrywania gotowości HTTP, drugi pokazuje środowisko uruchomieniowe, a trzeci wykonuje niewielką pracę obliczeniową.

Najważniejsze fragmenty `Program.cs`:

```csharp
using System.Diagnostics;
using System.Runtime.InteropServices;

var startupTimer = Stopwatch.StartNew();
var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://127.0.0.1:5080");

var app = builder.Build();

app.MapGet("/ping", () => Results.Ok(new
{
    Status = "OK",
    Message = "StartupWebApi is running",
    Timestamp = DateTimeOffset.UtcNow
}));

app.MapGet("/runtime", () => Results.Ok(new
{
    Framework = RuntimeInformation.FrameworkDescription,
    OS = RuntimeInformation.OSDescription,
    Architecture = RuntimeInformation.ProcessArchitecture.ToString(),
    ProcessId = Environment.ProcessId,
    ProcessorCount = Environment.ProcessorCount,
    Is64BitProcess = Environment.Is64BitProcess
}));

app.MapGet("/work", () =>
{
    var timer = Stopwatch.StartNew();
    long sum = 0;
    for (int i = 0; i < 1_000_000; i++) sum += i;
    timer.Stop();
    return Results.Ok(new
    {
        Result = sum,
        ElapsedMs = timer.Elapsed.TotalMilliseconds
    });
});

app.Lifetime.ApplicationStarted.Register(() =>
{
    startupTimer.Stop();
    Console.WriteLine($"Startup time: {startupTimer.Elapsed.TotalMilliseconds:F3} ms");
});

await app.RunAsync();
```

**Uwaga o granicach pomiaru:** `startupTimer` startuje na początku `Program.cs`, a zatrzymuje się przy `ApplicationStarted`. Nie obejmuje inicjalizacji procesu i runtime przed wejściem do kodu zarządzanego.

## 4. `dotnet run`: co uruchamia się po kolei?

```powershell
dotnet run --no-build --no-launch-profile
```

`--no-build` pomija kompilację, a `--no-launch-profile` pomija ustawienia z `launchSettings.json`.

W uproszczeniu:

1. **.NET CLI / host aplikacji** inicjuje uruchomienie procesu i wybór środowiska .NET. W mechanizmach hostowania uczestniczą m.in. `hostfxr` i `hostpolicy`.
2. **CoreCLR** inicjalizuje środowisko wykonawcze, obsługę zestawów, pamięci, wyjątków i JIT.
3. **JIT** kompiluje potrzebne fragmenty IL do instrukcji procesora. Nie wszystko musi zostać skompilowane przy starcie; kod może być kompilowany także przy pierwszych żądaniach.
4. **`Program.cs`** tworzy `WebApplicationBuilder`, konfiguruje aplikację i rejestruje endpointy.
5. **ASP.NET Core i Kestrel** uruchamiają host i nasłuchiwanie HTTP.
6. **Klient HTTP** wysyła `GET /ping` i odbiera odpowiedź 200.

![Ścieżka uruchamiania Web API i granice dwóch pomiarów](/images/webapi-dotnet10-sciezka-startu.svg)

Na diagramie zaznaczyłem dwie różne miary. Wewnętrzna kończy się na `ApplicationStarted`; zewnętrzna kończy się dopiero wtedy, gdy skrypt testowy odbierze HTTP 200. To nie są zamienne wartości.

## 5. Pierwsza obserwacja: 2542 ms

Pojedyncze uruchomienie Debug zwróciło:

```text
Framework: .NET 10.0.14
Architecture: X64
Process ID: 21332
Startup time: 2542,255 ms
```

Ten wynik był znacznie wyższy od kolejnych pomiarów. Jedna próba nie wystarcza do oceny typowego czasu startu ani do przypisania opóźnienia JIT. Dlatego wykonałem serię powtórzeń.

## 6. Eksperyment: 60 niezależnych uruchomień

Skrypt PowerShell uruchamiał aplikację w osobnym procesie, próbował połączyć się z `http://127.0.0.1:5080/ping`, a następnie zatrzymywał proces. Rejestrował:

- **StartupToHttp200Ms** — czas od rozpoczęcia procedury `Start-Process` do odebrania HTTP 200;
- **ManagedStartupMs** — czas zgłaszany przez aplikację od początku `Program.cs` do `ApplicationStarted`;
- status uruchomienia i dane diagnostyczne.

Buildy Debug i Release przygotowano **przed** pomiarem; czas kompilacji nie wchodził do wyników. Próby wykonano kolejno dla konfiguracji, nie w losowej kolejności przeplatanej.

### Wyniki

| Metryka | Debug | Release |
|---|---:|---:|
| Próby | 30 | 30 |
| Poprawne HTTP 200 | 30 | 30 |
| Mediana do HTTP 200 | **674,04 ms** | **676,07 ms** |
| P95 do HTTP 200 | 1210,25 ms | 1179,24 ms |
| Minimum do HTTP 200 | 645,94 ms | 650,47 ms |
| Maksimum do HTTP 200 | 1522,95 ms | 1182,08 ms |
| Mediana czasu wewnętrznego | **251,41 ms** | **251,27 ms** |
| P95 czasu wewnętrznego | 374,08 ms | 352,81 ms |

![Wyniki 60 uruchomień ASP.NET Core Web API: Debug i Release](/images/webapi-dotnet10-wyniki-60-prob.svg)

Różnica median czasu do HTTP 200 wynosi **2,03 ms**, czyli około **0,3%**. W tym konkretnym teście nie zaobserwowaliśmy praktycznej przewagi Release pod względem gotowości niewielkiego Web API.

Nie jest to dowód, że konfiguracje Debug i Release mają identyczną wydajność we wszystkich zastosowaniach. Build Debug uruchomiony bez debuggera nie jest też równoważny działaniu aplikacji pod aktywnym debuggerem.

### Skąd różnica między około 251 a 675 ms?

Pomiar wewnętrzny zaczyna się dopiero w `Program.cs` i kończy przy `ApplicationStarted`. Pomiar zewnętrzny obejmuje również wywołanie `Start-Process`, inicjalizację procesu i runtime, sprawdzanie gotowości, obsługę żądania oraz narzut klienta PowerShell.

**Nie można odjąć median i nazwać otrzymanej różnicy „kosztem JIT” lub „kosztem CoreCLR”.** Mediany są statystykami dwóch różnych miar; bez dodatkowej instrumentacji nie znamy dokładnego udziału poszczególnych etapów.

Aby rozłożyć czas na komponenty, należałoby wykorzystać np. ETW, EventPipe lub precyzyjne znaczniki czasu rejestrowane w kilku punktach uruchamiania.

## 7. Pierwsze żądanie a następne

W osobnym krótkim teście wywołałem dziesięć razy endpoint `/work`. Czas obliczeń zgłaszany przez serwer mieścił się od 1,06 do 3,72 ms, a czas po stronie klienta od 3,63 do 33,66 ms.

Przykładowo w drugiej próbie klient zmierzył **33,66 ms**, podczas gdy sama mierzona pętla na serwerze trwała **2,05 ms**. To pokazuje, że czas HTTP nie jest czasem pojedynczej metody.

Zmiany czasu obliczeń mogą być zgodne z rozgrzewaniem kodu i optymalizacjami runtime, ale na podstawie dziesięciu prób nie można wykazać, że konkretną przyczyną była Tiered Compilation.

## 8. `dotnet run`, `dotnet DLL` czy `EXE`?

Do pracy deweloperskiej wygodny jest `dotnet run`:

```powershell
dotnet run --no-build --no-launch-profile
```

Można jednak uruchomić również sam zestaw:

```powershell
dotnet .\bin\Release\net10.0\StartupWebApi.dll
```

albo host aplikacji:

```powershell
.\bin\Release\net10.0\StartupWebApi.exe
```

W benchmarku 60 prób użyto bezpośredniego uruchamiania `StartupWebApi.exe`, aby nie włączać narzutu narzędzia `dotnet run` do mierzonej ścieżki. Nadal jest to zwykła aplikacja korzystająca z CoreCLR, a nie automatycznie aplikacja Native AOT.

## 9. Ograniczenia i następny krok

Nie testowałem tu ReadyToRun, Native AOT, publikacji self-contained, uruchamiania w kontenerze, obciążenia równoległego ani kosztów startu pod debuggerem. Na wynik mogły wpływać cache systemu, antywirus i aktywność innych procesów.

Co ustaliliśmy?

1. `dotnet build` i uruchomienie aplikacji to dwa różne etapy; standardowa kompilacja generuje IL, a JIT może przygotowywać kod maszynowy podczas wykonania.
2. `ApplicationStarted` i pierwsze HTTP 200 wyznaczają **różne granice pomiaru**.
3. W naszym niewielkim Web API mediany czasu do HTTP 200 były niemal identyczne: **674,04 ms Debug** i **676,07 ms Release**.
4. Jeden wolny start nie jest wystarczającym dowodem na koszt JIT — potrzebne są serie pomiarowe i diagnostyka.

Następnym naturalnym eksperymentem będzie uruchomienie tej samej aplikacji w wariantach JIT, ReadyToRun i Native AOT. Dopiero takie porównanie pozwoli sprawdzić, czy wcześniejsze przygotowanie kodu natywnego skraca czas do pierwszego HTTP 200.

---

*Eksperyment: 7 listopada 2026 r. Dane źródłowe: `webapi-startup-raw-20261107-213449.csv` i `webapi-startup-summary-20261107-213449.csv`. Łącznie 60/60 poprawnych uruchomień.*
