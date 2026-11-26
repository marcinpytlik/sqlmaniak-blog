---
title: "EF Core oczami DBA – uśpiona sesja, wyczerpana pula i otwarta transakcja"
date: 2026-11-27T08:00:00+01:00
draft: false
translationKey: "ef-core-connection-pool-exhaustion"
description: "Pięć eksperymentów z EF Core 10, SqlClient i SQL Server 2022: wyczerpanie puli, blokowanie i reset sesji."
categories: ["EF Core oczami DBA", "SQL Server"]
tags: ["EF Core 10", "SQL Server 2022", "Connection Pooling", "Microsoft.Data.SqlClient", "Extended Events", "DMV", "Blocking"]
---

## SQL Server odpowiada, a aplikacja nie działa

Wyobraźmy sobie zgłoszenie produkcyjne: użytkownicy nie mogą korzystać z aplikacji, która zgłasza timeouty. DBA sprawdza aktywne requesty, blokowanie i otwarte transakcje. Sesje aplikacji są w stanie `sleeping`, a silnik odpowiada na zapytania diagnostyczne. Gdzie szukać przyczyny?

Być może po niewłaściwej stronie architektury. Inspiracją do tego laboratorium był artykuł Hannah Vernon [Connection Pool Exhaustion](https://www.sqlserverscience.com/troubleshooting/connection-pool-exhaustion/). Postanowiłem odtworzyć część jej obserwacji na współczesnym stosie .NET 10 i rozszerzyć eksperyment o telemetrię SqlClient, DMV, Extended Events oraz kontrolowany test blokowania.

## 1. Trzy różne cykle życia

Cykl życia `DbContext`, logicznego połączenia i fizycznej sesji SQL Server to trzy różne rzeczy. Connection Pooling pozwala wielokrotnie używać fizycznych połączeń, zamiast za każdym razem zestawiać transport i uwierzytelniać użytkownika. `Close()` lub `Dispose()` zazwyczaj zwraca połączenie do puli, jeśli pooling jest włączony i połączenie nadaje się do ponownego użycia.

Stan `sleeping` oznacza brak aktualnie wykonywanego requestu, nie dostępność połączenia w puli. SqlClient zarządza pulami po stronie procesu; SQL Server nie zna ich liczby wolnych miejsc. DbContext Pooling jest odrębnym mechanizmem od Connection Poolingu.

## 2. Środowisko i metodyka

| Komponent | Wersja |
|---|---|
| SQL Server | 2022 Developer CU28, 16.0.4325.4 |
| System kontenera | Ubuntu 22.04.5 LTS |
| .NET | 10 |
| EF Core | 10.0.15 |
| Microsoft.Data.SqlClient | 6.1.7 (assembly 6.0.0.0) |
| SNI Runtime | 6.0.3 |
| dotnet-counters | 10.0.750501 |
| Środowisko | Docker Desktop, PowerShell 7 |
| Data pomiarów | 2026-11-26 |

W odizolowanym kontenerze użyłem bazy `tempdb` i celowo małej puli. To konfiguracja badawcza, nie rekomendacja produkcyjna.

```csharp
var cs = new SqlConnectionStringBuilder
{
    DataSource = "127.0.0.1,15468",
    InitialCatalog = "tempdb",
    UserID = "sa",
    Password = password,
    TrustServerCertificate = true,
    ApplicationName = "SQLManiak.Lab68",
    MaxPoolSize = 3,
    ConnectTimeout = 5,
    ConnectRetryCount = 0,
    Pooling = true
}.ConnectionString;
```

Pięć scenariuszy: A – baseline, B – wyczerpanie puli, C – transakcja po Dispose, D – blokowanie po Dispose, E – jawny rollback. Zbieram dane na trzech poziomach: aplikacja, SqlClient i silnik SQL Server. Czas CSV z lokalnej strefy CET przeliczam na UTC.

## 3. Eksperyment A – Baseline

Każda z dziesięciu sekwencyjnych operacji tworzy nowy kontekst:

```csharp
await using var db = new LabContext(options);
var spid = await db.Database
    .SqlQueryRaw<int>("SELECT CAST(@@SPID AS int) AS Value")
    .SingleAsync();
```

| Operacja | SPID | Czas (ms) |
|---:|---:|---:|
| 1 | 53 | 590 |
| 2 | 53 | 25 |
| 3 | 53 | 83 |
| 4 | 53 | 2 |
| 5 | 53 | 2 |
| 6 | 53 | 2 |
| 7 | 53 | 2 |
| 8 | 53 | 1 |
| 9 | 53 | 2 |
| 10 | 53 | 2 |

![Czasy operacji baseline](/images/lab68/01-baseline.svg)

*Rysunek 1. Rzeczywiste pomiary, skala logarytmiczna.*

Wszystkie operacje zakończyły się sukcesem, mediana wyniosła 2 ms. Identyczny SPID w sekwencji jest zgodny z ponownym użyciem sesji. Pierwsze 590 ms obejmuje potencjalnie inicjalizację EF Core, JIT i zestawienie połączenia; nie jest izolowanym pomiarem kosztu logowania.

## 4. Eksperyment B – Connection Pool Exhaustion

Trzy konteksty jawnie otwierają połączenia (`await db.Database.OpenConnectionAsync();`) i nie zwalniają ich po zakończeniu zapytań. Czwarta próba musi czekać na wolne miejsce w puli.

W jednym wykonaniu DMV pokazały SPID 60, 62 i 63: wszystkie `sleeping`, `open_transaction_count=0`, bez aktywnych requestów i bez blokowania w próbkach. Mimo to aplikacja zgłosiła `InvalidOperationException` z komunikatem o upływie limitu czasu przed uzyskaniem połączenia z puli.

| Metryka | Pomiar 1 | Pomiar 2 |
|---|---:|---:|
| Connect Timeout (ms) | 5000 | 5000 |
| Timeout (ms) | 5021 | 5015 |
| Recovery (ms) | 5 | 6 |
| SPID recovery | 63 | 70 |

Po zwolnieniu trzech kontekstów kolejny odczyt zakończył się sukcesem bez restartu aplikacji ani SQL Server. Oczekiwanie na miejsce w puli nie musi generować requestu na serwerze. Nie jest to timeout wykonywania polecenia SQL.

### EventCounters – dowód po stronie klienta

Provider: `Microsoft.Data.SqlClient.EventSource`. Zebrano 60 próbek czterech liczników (240 wartości). W powtórzeniu B zajęte były SPID 68, 69, 70.

| Przedział UTC (włącznie) | Próbki | Active | Ready | Pooled | Pools |
|---|---:|---:|---:|---:|---:|
| 21:20:05–21:20:54 | 50 | 3 | 0 | 3 | 1 |
| 21:20:55–21:21:04 | 10 | 0 | 3 | 3 | 1 |

Timeout nastąpił o 21:20:40.081 UTC, zwolnienie połączeń o 21:20:55.102 UTC. Recovery trwało 6 ms i jego chwilowy checkout nie został uchwycony w sekundowym próbkowaniu.

![Wyczerpanie i odzyskanie puli](/images/lab68/02-pool-exhaustion.svg)

*Rysunek 2. Rzeczywiste próbki EventCounters, czas UTC.*

Liczba połączeń zarządzanych przez pulę pozostała równa trzy. Dostępność zmieniła się z zera do trzech. To, czego nie możemy ustalić na podstawie samego statusu sesji SQL Server, widzimy bezpośrednio w telemetrii procesu aplikacyjnego.

## 5. Eksperyment C – Transaction after Dispose

Co się stanie, gdy rozpocznę transakcję bezpośrednio przez T-SQL, a następnie zwolnię obiekt połączenia?

```csharp
await using (var c = new SqlConnection(cs))
{
    await c.OpenAsync();
    await using var cmd = c.CreateCommand();
    cmd.CommandText = "BEGIN TRANSACTION; SELECT @@SPID;";
    Console.WriteLine(await cmd.ExecuteScalarAsync());
}
```

Celowo nie wykonuję COMMIT ani ROLLBACK. Przez około 30 sekund obserwuję sesję, a następnie ponownie pobieram połączenie.

| Czas UTC | Obserwacja |
|---|---|
| 21:03:32.273 | connect_time SPID 53 |
| 21:03:32.363 | Początek transakcji 13578 |
| 21:03:33.400 | sleeping, open_transaction_count=1 |
| 21:04:02.002 | Ostatnia próbka aktywnej transakcji |
| 21:04:02.922 | Kolejna operacja aplikacji zakończona sukcesem |
| 21:04:03.101 | Pierwsza próbka open_transaction_count=0 |

![Transakcja po Dispose](/images/lab68/03-transaction-after-dispose.svg)

*Rysunek 3. Próbki DMV; moment zmiany ograniczony przedziałem próbkowania.*

W 27 próbkach transakcja była aktywna (state 2), w kolejnych 14 już jej nie było. SPID i connect_time pozostały takie same. W tej konfiguracji transakcja T-SQL przetrwała Dispose i zniknęła przy ponownym użyciu połączenia. Nie wykonywałem tu modyfikacji danych; wpływ na blokowanie sprawdziłem osobno.

## 6. Eksperyment D – Blokowanie po Dispose

W `tempdb` tworzę tabelę o unikalnej nazwie i początkowej wartości `V=0`. Przykładowy T-SQL sesji właściciela:

```sql
BEGIN TRANSACTION;
UPDATE dbo.Lab68_Test SET V = 1 WHERE Id = 1;
```

Po Dispose druga sesja, z niezależnym niepoolowanym połączeniem, wykonuje:

```sql
SELECT V FROM dbo.Lab68_Test WITH (READCOMMITTEDLOCK)
WHERE Id = 1;
```

Hint wymusza odczyt oparty na blokadach również przy RCSI. Nazwa tabeli w faktycznym kodzie jest generowana dynamicznie.

| Parametr | Właściciel | Obserwator |
|---|---|---|
| SPID | 60 | 59 |
| Session status | sleeping | running |
| Request status | NULL | suspended |
| Open transactions | 1 | 0 |
| Wait type | NULL | LCK_M_S |
| Blocking session ID | NULL | 60 |

Dziewięć kolejnych próbek pokazało tę zależność. Po 10 sekundach odczyt obserwatora nadal oczekiwał. Ponowne użycie SPID 60 dało `@@TRANCOUNT=0`, a obserwator otrzymał pierwotną wartość 0. To potwierdza wycofanie zmiany i ustąpienie blokowania.

![Łańcuch blokowania](/images/lab68/04-blocking-chain.svg)

*Rysunek 4. Diagram mechanizmu potwierdzonego pomiarami.*

## 7. Extended Events – reset sesji

Zdarzenia `login`, `logout`, `rpc_completed` i `sql_batch_completed` pozwoliły odtworzyć sekwencję właściciela:

| UTC | Zdarzenie |
|---|---|
| 21:13:50.678 | login, is_cached=false |
| 21:13:50.681 | SELECT @@SPID |
| 21:13:50.693 | BEGIN TRANSACTION + UPDATE |
| 21:13:50.698 | Dispose w logu aplikacji |
| 21:14:00.711 | logout, is_cached=true |
| 21:14:00.711 | rpc_completed: sp_reset_connection |
| 21:14:00.711 | login, is_cached=true |
| 21:14:00.712 | SELECT @@SPID, @@TRANCOUNT |
| 21:14:00.715 | Odczyt obserwatora zakończony (log aplikacji) |

Reset SPID 60 trwał według XE 281 µs, wynik OK. Ring buffer raportował osiem zdarzeń, droppedCount=0 i truncated=0. Obserwator pozostawał poza filtrem XE; jego zakończenie potwierdza log aplikacji. Zdarzenia cached login/logout nie oznaczają tutaj nowego fizycznego połączenia.

Reset przy ponownym użyciu połączenia, zniknięcie transakcji i odczyt wartości 0 są spójnymi dowodami mechanizmu. Nie obserwowaliśmy resetu w momencie wcześniejszego Dispose.

## 8. Eksperyment E – Explicit Rollback

Wariant kontrolny rozpoczyna transakcję przez API SqlClient i jawnie ją wycofuje przed zwolnieniem połączenia:

```csharp
await using var tx = (SqlTransaction)await owner.BeginTransactionAsync();
// UPDATE z przypisaniem tx do SqlCommand.Transaction
await tx.RollbackAsync();
```

| Parametr | D – Blocking | E – Rollback |
|---|---|---|
| UPDATE | Tak | Tak |
| Jawny rollback | Nie | Tak |
| Odczyt oczekuje po 10 s | Tak | Nie |
| LCK_M_* w próbkach | LCK_M_S | Brak |
| TRANCOUNT po reuse | 0 | 0 |
| Wartość odczytana | 0 | 0 |

Pierwotne wartości 10014 i 10012 ms obejmowały celowe okno obserwacji. Nie są porównywalnymi pomiarami izolowanego SELECT. Poprawiono kod pomiarowy, ale ponowny test tej poprawki pozostaje do wykonania. Kontrola zmienia zarówno sposób rozpoczęcia transakcji, jak i jawność rollbacku, więc nie izoluje osobno wpływu obu czynników.

## 9. Diagnostyka produkcyjna

```sql
SELECT SYSUTCDATETIME() AS ObservationUTC,
       s.session_id, s.host_name, s.program_name, s.login_name,
       s.status AS SessionStatus, s.open_transaction_count,
       r.status AS RequestStatus, r.wait_type, r.wait_time,
       r.blocking_session_id, c.connect_time,
       s.last_request_start_time, s.last_request_end_time
FROM sys.dm_exec_sessions AS s
LEFT JOIN sys.dm_exec_requests AS r ON s.session_id = r.session_id
LEFT JOIN sys.dm_exec_connections AS c ON s.session_id = c.session_id
WHERE s.is_user_process = 1
ORDER BY s.open_transaction_count DESC, s.session_id;
```

Uśpione sesje z otwartymi transakcjami można wyodrębnić:

```sql
SELECT session_id, host_name, program_name, login_name,
       open_transaction_count, last_request_end_time,
       DATEDIFF(SECOND, last_request_end_time, SYSDATETIME()) AS IdleSeconds
FROM sys.dm_exec_sessions
WHERE is_user_process = 1 AND status = N'sleeping'
  AND open_transaction_count > 0
ORDER BY IdleSeconds DESC;
```

Wymagane są odpowiednie uprawnienia do DMV (w SQL Server 2022 zwykle VIEW SERVER PERFORMANCE STATE). Ustalenie sesji nie jest automatycznym wskazaniem do KILL. Najpierw należy określić właściciela, wiek transakcji, blokowane zasoby i skutki ewentualnego rollbacku.

Otwarte transakcje mogą powodować blokowanie, opóźniać ponowne wykorzystanie logu, a w odpowiednich scenariuszach izolacji utrzymywać wersje wierszy. Długotrwałe blokowanie może z kolei zwiększać czas zajęcia połączeń i wyczerpać pulę. Nie mierzyłem jednak wzrostu logu, Version Store ani takiej kaskady w Lab 68.

## 10. Rekomendacje dla .NET i DBA

Otwieraj połączenia możliwie późno i zwalniaj je możliwie wcześnie. Nie utrzymuj ich podczas niezwiązanych operacji HTTP. Zarządzaj transakcjami świadomie, z COMMIT na ścieżce sukcesu i odpowiednim rollbackiem na ścieżce błędu; preferuj API EF Core lub ADO.NET. Nie polegaj na przyszłym resecie sesji jako strategii sprzątania.

Zwiększenie Max Pool Size może być uzasadnione obciążeniem, ale nie naprawia nieprawidłowego cyklu życia połączeń. Monitoruj liczbę Active/Ready/Pooled, liczbę pul, czas pobierania połączenia, wyjątki i czas transakcji. Koreluj je z DMV i XE. Pooling DbContext nie zastępuje zarządzania pulą SqlClient.

![Trzy perspektywy diagnostyczne](/images/lab68/05-diagnostic-perspectives.svg)

*Rysunek 5. Metodyka diagnostyczna – diagram poglądowy.*

## 11. Reprodukcja

Kod: [SQLManiak Lab 68 – PR #146](https://github.com/marcinpytlik/SQLManiak/pull/146). W odizolowanym labie z Docker, .NET 10, PowerShell 7, sqlcmd i dotnet-counters:

```powershell
cd labs\68_ConnectionPoolExhaustion
$env:LAB_PASSWORD = Read-Host "Hasło SA" -MaskInput
docker compose up -d
# Poczekaj na gotowość SQL Server przed uruchomieniem testu.
.\Invoke-Lab68.ps1 -Counters -XE
# Wybrane scenariusze:
.\Invoke-Lab68.ps1 -Scenario exhaustion -Counters -XE
.\Invoke-Lab68.ps1 -Scenario blocking,rollback -XE
```

Skrypt zapisuje logi aplikacji, DMV, XE, liczniki i wersje pakietów w oddzielnym katalogu wynikowym. Po zakończeniu `docker compose down` i `Remove-Item Env:\LAB_PASSWORD`. Użycie SA i TrustServerCertificate jest ograniczone do środowiska laboratoryjnego.

## 12. Ograniczenia i podsumowanie

Badania wykonano lokalnie z małą pulą, określonym providerem i wymuszonym odczytem blokadowym. Próbkowanie nie jest ciągłym śledzeniem; wyników nie można automatycznie uogólniać na wszystkie wersje bibliotek i API transakcji. To badanie mechanizmu, nie benchmark przepustowości.

Pięć obserwacji: kolejne DbContext mogą współdzielić fizyczną sesję; sleeping nie oznacza wolnego połączenia; wyczerpanie puli nie musi generować requestu SQL; transakcja rozpoczęta w T-SQL może przetrwać Dispose; uśpiona sesja może blokować innych użytkowników. W badanej konfiguracji XE potwierdziły reset przy ponownym wykorzystaniu, a EventCounters pokazały odzyskanie dostępności puli.

Współczesny DBA musi rozumieć nie tylko to, co dzieje się w bazie, ale również to, co dzieje się pomiędzy aplikacją a bazą danych.

**SQLManiak – mniej teorii, więcej dowodów.**

## Materiały

- [Hannah Vernon – Connection Pool Exhaustion](https://www.sqlserverscience.com/troubleshooting/connection-pool-exhaustion/)
- [SQLManiak – Lab 68](https://github.com/marcinpytlik/SQLManiak/pull/146)
- [Microsoft Learn – SQL Server connection pooling](https://learn.microsoft.com/en-us/sql/connect/ado-net/sql-server-connection-pooling)
- [Microsoft Learn – dotnet-counters](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters)
