---
title: "Od kontenera do HTTP 200. ASP.NET Core Web API w .NET 10 na Docker i Kubernetes"
date: 2026-11-08T14:00:00+01:00
slug: "od-kontenera-do-http-200-dotnet10-docker-kubernetes"
description: "Ta sama aplikacja ASP.NET Core Web API w .NET 10, dwa środowiska: Docker i Kubernetes. Jak mierzyć start procesu, kontenera, Pod Ready i pierwsze HTTP 200?"
category: ".NET"
tags:
  - .NET 10
  - ASP.NET Core
  - Docker
  - Kubernetes
  - Kestrel
  - performance
  - benchmarking
draft: false
---

# Od kontenera do HTTP 200. ASP.NET Core Web API w .NET 10 na Docker i Kubernetes

W [poprzednim eksperymencie](/posts/anatomia-uruchamiania-aspnet-core-webapi-dotnet10/) uruchamiałem niewielkie ASP.NET Core Web API na Windows 11. Mierzyłem czas od uruchomienia procesu do pierwszej odpowiedzi HTTP 200 oraz czas zgłaszany przez samą aplikację przy `ApplicationStarted`.

Tym razem nie zmieniam logiki aplikacji. Zmieniam środowisko uruchomieniowe: najpierw **Docker**, potem **Kubernetes w Docker Desktop**.

Pytanie brzmi nie tylko „ile trwa start?”, lecz także: **co dokładnie uznajemy za zakończenie uruchamiania?** W kontenerze i w Kubernetes odpowiedź okazuje się mniej oczywista.

> To opis eksperymentu na jednym komputerze, nie ranking Docker kontra Kubernetes. Różne mechanizmy publikacji portu i obserwowania gotowości mogą wpływać na wyniki.

## Środowisko

| Element | Konfiguracja |
|---|---|
| Host | Windows 11 Pro, build 26300 |
| CPU | Intel Core i5-1035G1, 4 rdzenie / 8 procesorów logicznych |
| RAM | 7,81 GiB |
| PowerShell | 7.6.9 |
| .NET w kontenerze | 10.0.14, Linux x64 |
| Docker Desktop | 29.9.2 |
| Kubernetes | v1.36.1, kontekst `docker-desktop` |
| Węzeł | `desktop-control-plane`, Debian 13, containerd 2.3.1 |
| Obraz aplikacji | `startupwebapi:1.0` |
| Endpoint testowy | `GET /ping`, port 5080 |

Aplikacja nie korzysta z bazy danych. Chciałem oddzielić start hosta ASP.NET Core i Kestrela od kosztów inicjalizacji połączeń z zewnętrznymi usługami.

## 1. Ta sama aplikacja, inne otoczenie

Aplikacja udostępnia trzy endpointy: `/ping`, `/runtime` i `/work`. Do wykrywania gotowości używam pierwszego z nich.

W `Program.cs` rejestruję czas od początku wykonywania kodu zarządzanego do zdarzenia `ApplicationStarted`:

```csharp
var startupTimer = Stopwatch.StartNew();
var builder = WebApplication.CreateBuilder(args);

builder.WebHost.UseUrls("http://0.0.0.0:5080");

var app = builder.Build();

app.MapGet("/ping", () => Results.Ok(new
{
    Status = "OK",
    Message = "StartupWebApi is running",
    Timestamp = DateTimeOffset.UtcNow
}));

app.Lifetime.ApplicationStarted.Register(() =>
{
    startupTimer.Stop();
    Console.WriteLine(
        $"Startup time: {startupTimer.Elapsed.TotalMilliseconds:F3} ms");
});

await app.RunAsync();
```

W kontenerze używam `0.0.0.0`, a nie `127.0.0.1`. Dzięki temu Kestrel nasłuchuje na interfejsach kontenera i może odbierać ruch przekazywany przez Docker lub Kubernetes.

**Uwaga:** pomiar `Startup time` nie obejmuje całej inicjalizacji procesu .NET przed wejściem do `Program.cs`.

## 2. Docker: od obrazu do działającego Kestrela

Zbudowałem obraz wieloetapowo: SDK .NET 10 służy do kompilacji i publikacji, a końcowy kontener korzysta z obrazu ASP.NET Core Runtime 10.

Uproszczony `Dockerfile`:

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app/publish .
EXPOSE 5080
ENTRYPOINT ["dotnet", "StartupWebApi.dll"]
```

W projekcie .NET warto dodać do `.dockerignore` przynajmniej katalogi `bin` i `obj`. Podczas przygotowywania eksperymentu przekopiowanie lokalnych artefaktów kompilacji do kontenera spowodowało błąd `NETSDK1064`. Wykluczenie tych katalogów rozwiązało problem.

Budowa i uruchomienie:

```powershell
docker build -t startupwebapi:1.0 .
docker run --rm -p 5080:5080 startupwebapi:1.0
Invoke-RestMethod http://127.0.0.1:5080/ping
```

W pomiarach automatycznych skrypt przydzielał dynamiczny port hosta, aby kolejne uruchomienia nie kolidowały ze sobą.

Co mierzyłem? Stoper po stronie PowerShell startował **przed** wywołaniem `docker run`, a zatrzymywał się po odebraniu pierwszego HTTP 200. Obejmuje to więc również uruchomienie klienta Docker, operacje demona, publikację portu i odpytywanie HTTP.

## 3. Kubernetes: Running to jeszcze nie Ready

Ten sam obraz zaimportowałem do środowiska `containerd` klastra Docker Desktop. W eksperymencie użyłem `imagePullPolicy: Never`, aby nie pobierać obrazu podczas każdej próby.

Przykładowa definicja kontenera:

```yaml
containers:
  - name: startupwebapi
    image: startupwebapi:1.0
    imagePullPolicy: Never
    ports:
      - containerPort: 5080
    readinessProbe:
      httpGet:
        path: /ping
        port: 5080
      periodSeconds: 1
      timeoutSeconds: 1
      failureThreshold: 3
```

Każda próba tworzyła osobny Pod, bez modyfikowania istniejącego Deploymentu.

W Kubernetes pojawia się kilka różnych zdarzeń:

1. Żądanie utworzenia Poda trafia do API.
2. Scheduler przydziela Pod do węzła.
3. Runtime uruchamia kontener.
4. Proces .NET uruchamia aplikację i Kestrel.
5. Sonda readiness uzyskuje poprawną odpowiedź.
6. Kubernetes raportuje `Pod Ready=True`.

**`Pod Running` nie oznacza, że aplikacja przyjmuje już żądania HTTP.** Przekonałem się o tym również podczas tworzenia benchmarku.

Próba uruchomienia `kubectl port-forward`, gdy Pod był jeszcze `Pending`, kończyła się komunikatem:

```text
unable to forward port because pod is not running.
Current status=Pending
```

Po zmianie skryptu na oczekiwanie na `Running` pojawił się jeszcze jeden przypadek: Pod już działał, ale Kestrel nie rozpoczął nasłuchiwania, więc połączenie do portu 5080 zostało odrzucone. To nie dowód awarii aplikacji, lecz przykład wyścigu pomiędzy etapami uruchamiania.

## 4. Pierwsze pomiary: gotowość Poda

Najpierw wykonałem serię **30 pomiarów Kubernetes**, z trzema próbami rozgrzewkowymi. Wszystkie 30 prób pomiarowych zakończyły się osiągnięciem stanu Ready.

| Metryka | Mediana | P95 |
|---|---:|---:|
| Klient PowerShell → zaobserwowane Pod Ready | 3 809,34 ms | 6 722,64 ms |
| Utworzenie Poda → Ready według znaczników Kubernetes | 3 000 ms | 5 550 ms |
| Start zarządzany .NET | 739,59 ms | 1 379,49 ms |

Znaczniki zdarzeń Kubernetes mają w tym zestawie rozdzielczość rzędu sekund. Nie należy zatem traktować różnic wyliczonych z tych znaczników jako pomiarów z dokładnością do milisekundy.

Co więcej, **Pod Ready i pierwsze HTTP 200 zaobserwowane przez zewnętrznego klienta nie są tym samym pomiarem**. Dlatego przeprowadziłem dodatkowy eksperyment.

## 5. Druga seria: pierwsze HTTP 200 w obu środowiskach

W serii kontrolnej zastosowałem tę samą aplikację, endpoint `/ping`, 30 prób pomiarowych na środowisko, trzy rozgrzewki i odpytywanie HTTP co 50 ms.

Dla Dockera klient łączył się z portem opublikowanym na hoście. Dla Kubernetes wykorzystywałem `kubectl port-forward`, uruchamiany po przejściu Poda do `Running`. Stoper startował jednak przed żądaniem utworzenia Poda.

### Wyniki serii kontrolnej

| Statystyka | Docker | Kubernetes |
|---|---:|---:|
| Udane próby | 30/30 | 29/30 |
| Mediana do HTTP 200 | **1 921,12 ms** | **2 671,71 ms** |
| Średnia do HTTP 200 | 2 005,58 ms | 3 059,45 ms |
| P95 do HTTP 200 | 2 699,60 ms | 5 526,20 ms |
| Maksimum do HTTP 200 | 2 785,88 ms | 6 603,94 ms |
| Mediana startu zarządzanego .NET | 721,56 ms | 632,08 ms |

W udanych próbach mediana czasu do HTTP 200 była w Kubernetes wyższa o około **751 ms (39%)**. Różnica w P95 była większa: około **2,83 sekundy**.

Nie oznacza to, że „Kubernetes dodaje 751 ms”. Porównuję dwie różne ścieżki sieciowe: opublikowany port Dockera i tunel `kubectl port-forward`. W wyniku Kubernetes zawiera się również zestawienie tunelu oraz narzut operacji wykonywanych przez `kubectl`.

Jedna z 30 prób Kubernetes nie zakończyła się sukcesem z powodu przedwczesnego przekazania połączenia na port, na którym aplikacja jeszcze nie nasłuchiwała. Statystyki czasowe Kubernetes dotyczą **29 udanych prób**; nieudanej próby nie zastępuję wartością zero ani nie ukrywam jej w liczbie sukcesów.

## 6. Dlaczego czas .NET i czas HTTP tak bardzo się różnią?

W ostatniej serii Docker potrzebował medianowo około **722 ms** od początku `Program.cs` do `ApplicationStarted`, a klient obserwował HTTP 200 po około **1 921 ms**.

W Kubernetes odpowiednie mediany wyniosły około **632 ms** i **2 672 ms**.

Nie odejmuję tych median i nie nazywam różnicy kosztem konteneryzacji czy orkiestracji. To różne zegary i różne granice pomiaru. Zewnętrzny pomiar obejmuje m.in. uruchomienie narzędzia, działania runtime kontenerów, obserwowanie stanu i obsługę połączenia HTTP.

Ciekawa jest też odwrotna kolejność median wewnętrznych: w tej serii start zarządzany .NET w Kubernetes był krótszy niż w Dockerze. Nie dowodzi to, że Kubernetes przyspiesza .NET. Wpływ mogą mieć obciążenie hosta, planowanie CPU i warunki kolejnych prób.

## 7. Trzy lekcje z eksperymentu

**Po pierwsze: trzeba nazwać punkt końcowy pomiaru.** `ApplicationStarted`, `Container Started`, `Pod Running`, `Pod Ready` i HTTP 200 to różne zdarzenia.

**Po drugie: readiness probe ma znaczenie.** W Kubernetes gotowość Poda jest obserwowana przez mechanizm sond, którego częstotliwość wpływa na moment raportowania stanu Ready.

**Po trzecie: benchmark musi być równie starannie przygotowany jak aplikacja.** W trakcie testów poprawiałem obsługę opcjonalnych pól statusu Poda, argumenty `kubectl port-forward` i kolejność zestawiania tunelu. Błędy skryptu pomiarowego nie mogą być przedstawiane jako błędy platformy.

## 8. Co dalej?

Na tym etapie mam wyniki uruchamiania tej samej aplikacji na Windows, w Dockerze i w Kubernetes. Zebrane dane pokazują różnice między czasem działania samej aplikacji a czasem, w którym klient może z niej skorzystać.

Do pełnej analizy potrzebne będzie jeszcze precyzyjniejsze rozdzielenie kosztów uruchomienia procesu, kontenera, orkiestracji i ścieżki sieciowej. Dlatego nie ogłaszam zwycięzcy.

**Najważniejszy wniosek:** kiedy mówimy, że aplikacja „wystartowała”, powinniśmy najpierw ustalić, *dla kogo* jest już gotowa — dla runtime .NET, dla systemu kontenerowego, dla Kubernetes czy dla klienta HTTP.

---

*Eksperyment: 8 listopada 2026 r. Środowisko: Windows 11, Docker Desktop i lokalny Kubernetes. Wyniki dotyczą konkretnego komputera i opisanej metodologii; nie są uniwersalnym benchmarkiem platform.*
