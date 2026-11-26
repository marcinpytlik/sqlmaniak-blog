---
title: "EF Core aus Sicht eines DBA – eine inaktive Sitzung, ein erschöpfter Pool und eine offene Transaktion"
date: 2026-11-27T08:00:00+01:00
draft: false
translationKey: "ef-core-connection-pool-exhaustion"
description: "Fünf Experimente mit EF Core 10, SqlClient und SQL Server 2022: Pool-Erschöpfung, Blockierung und Sitzungsreset."
categories: ["EF Core aus Sicht eines DBA", "SQL Server"]
tags: ["EF Core 10", "SQL Server 2022", "Connection Pooling", "Microsoft.Data.SqlClient", "Extended Events", "DMV", "Blocking"]
---

## SQL Server antwortet, aber die Anwendung funktioniert nicht

Stellen wir uns eine Produktionsstörung vor: Benutzer können eine Anwendung nicht mehr nutzen, die wiederholt Timeouts meldet. Der DBA prüft aktive Requests, Blockierungen und offene Transaktionen. Die Anwendungssitzungen befinden sich im Status `sleeping`, und die Datenbank-Engine beantwortet Diagnoseabfragen. Wo liegt die Ursache?

Vielleicht suchen wir auf der falschen Seite der Architektur. Die Inspiration für dieses Labor war Hannah Vernons Artikel [Connection Pool Exhaustion](https://www.sqlserverscience.com/troubleshooting/connection-pool-exhaustion/). Ich wollte einen Teil ihrer Beobachtungen mit einem modernen .NET-10-Technologiestack reproduzieren und das Experiment um SqlClient-Telemetrie, DMVs, Extended Events und einen kontrollierten Blockierungstest erweitern.

## 1. Drei unterschiedliche Lebenszyklen

Die Lebensdauer eines `DbContext`, einer logischen Verbindung und einer physischen SQL-Server-Sitzung sind drei unterschiedliche Dinge. Connection Pooling ermöglicht die Wiederverwendung physischer Verbindungen, statt jedes Mal die Netzwerkverbindung aufzubauen und den Benutzer zu authentifizieren. `Close()` oder `Dispose()` gibt eine Verbindung normalerweise an den Pool zurück, sofern Pooling aktiviert und die Verbindung wiederverwendbar ist.

Der Status `sleeping` bedeutet, dass gerade kein Request ausgeführt wird. Er sagt nichts darüber aus, ob die Verbindung im Pool verfügbar ist. SqlClient verwaltet Pools im Anwendungsprozess. SQL Server kennt die Zahl ihrer freien Plätze nicht. DbContext Pooling ist ein anderer Mechanismus als Connection Pooling.

## 2. Umgebung und Methodik

| Komponente | Version |
|---|---|
| SQL Server | 2022 Developer CU28, 16.0.4325.4 |
| Container-Betriebssystem | Ubuntu 22.04.5 LTS |
| .NET | 10 |
| EF Core | 10.0.15 |
| Microsoft.Data.SqlClient | 6.1.7 (Assembly 6.0.0.0) |
| SNI Runtime | 6.0.3 |
| dotnet-counters | 10.0.750501 |
| Umgebung | Docker Desktop, PowerShell 7 |
| Messdatum | 2026-11-26 |

In einem isolierten Container verwende ich `tempdb` und bewusst einen kleinen Verbindungspool. Dies ist eine Versuchskonfiguration, keine Empfehlung für den Produktivbetrieb.

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

Fünf Szenarien: A – Baseline, B – Pool-Erschöpfung, C – Transaktion nach Dispose, D – Blockierung nach Dispose, E – explizites Rollback. Ich erfasse Daten auf drei Ebenen: Anwendung, SqlClient und SQL Server. Die lokalen CSV-Zeitstempel in MEZ (CET) werden in UTC umgerechnet.

## 3. Experiment A – Baseline

Für jede der zehn sequenziellen Operationen wird ein neuer Kontext erstellt:

```csharp
await using var db = new LabContext(options);
var spid = await db.Database
    .SqlQueryRaw<int>("SELECT CAST(@@SPID AS int) AS Value")
    .SingleAsync();
```

| Operation | SPID | Zeit (ms) |
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

![Laufzeiten der Baseline-Operationen](/images/lab68/01-baseline.svg)

*Abbildung 1. Tatsächliche Messwerte, logarithmische Skala.*

Alle Operationen waren erfolgreich; der Median betrug 2 ms. Dieselbe SPID in der gesamten Sequenz spricht für die Wiederverwendung der Sitzung. Die anfänglichen 590 ms können die EF-Core-Initialisierung, JIT-Kompilierung und den Verbindungsaufbau umfassen. Sie sind keine isolierte Messung des Anmeldeaufwands.

## 4. Experiment B – Connection Pool Exhaustion

Drei Kontexte öffnen explizit Verbindungen (`await db.Database.OpenConnectionAsync();`) und behalten sie nach Abschluss ihrer Abfragen. Der vierte Versuch, eine Verbindung zu erhalten, muss auf einen freien Platz im Pool warten.

Bei einem Durchlauf zeigten die DMVs die SPIDs 60, 62 und 63: alle `sleeping`, `open_transaction_count=0`, ohne aktive Requests und ohne Blockierungen in den Stichproben. Dennoch meldete die Anwendung eine `InvalidOperationException`, weil das Zeitlimit vor dem Erhalt einer Verbindung aus dem Pool abgelaufen war.

| Messgröße | Durchlauf 1 | Durchlauf 2 |
|---|---:|---:|
| Connect Timeout (ms) | 5000 | 5000 |
| Gemessener Timeout (ms) | 5021 | 5015 |
| Recovery (ms) | 5 | 6 |
| SPID bei Recovery | 63 | 70 |

Nach Freigabe der drei Kontexte war die nächste Abfrage erfolgreich, ohne Neustart der Anwendung oder des SQL Servers. Das Warten auf einen freien Poolplatz muss keinen serverseitigen Request erzeugen. Es handelt sich nicht um einen Timeout bei der Ausführung eines SQL-Befehls.

### EventCounters – Nachweis auf Clientseite

Provider: `Microsoft.Data.SqlClient.EventSource`. Ich erfasste 60 Stichproben von vier Leistungsindikatoren (240 Werte). Bei der Wiederholung von B wurden die SPIDs 68, 69 und 70 belegt.

| UTC-Zeitraum (einschließlich) | Stichproben | Active | Ready | Pooled | Pools |
|---|---:|---:|---:|---:|---:|
| 21:20:05–21:20:54 | 50 | 3 | 0 | 3 | 1 |
| 21:20:55–21:21:04 | 10 | 0 | 3 | 3 | 1 |

Der Timeout trat um 21:20:40.081 UTC auf, die Verbindungen wurden um 21:20:55.102 UTC freigegeben. Die Recovery dauerte 6 ms; die kurze erneute Belegung wurde vom sekündlichen Abtastintervall nicht erfasst.

![Pool-Erschöpfung und Recovery](/images/lab68/02-pool-exhaustion.svg)

*Abbildung 2. Tatsächliche EventCounters-Stichproben, UTC.*

Die Anzahl der vom Pool verwalteten Verbindungen blieb bei drei. Die Verfügbarkeit stieg von null auf drei. Die Telemetrie des Anwendungsprozesses zeigt unmittelbar, was sich allein aus dem Sitzungsstatus des SQL Servers nicht ableiten lässt.

## 5. Experiment C – Transaktion nach Dispose

Was passiert, wenn ich eine Transaktion direkt über T-SQL starte und anschließend das Verbindungsobjekt freigebe?

```csharp
await using (var c = new SqlConnection(cs))
{
    await c.OpenAsync();
    await using var cmd = c.CreateCommand();
    cmd.CommandText = "BEGIN TRANSACTION; SELECT @@SPID;";
    Console.WriteLine(await cmd.ExecuteScalarAsync());
}
```

Ich führe bewusst weder COMMIT noch ROLLBACK aus. Ich beobachte die Sitzung etwa 30 Sekunden lang und beziehe danach erneut eine Verbindung.

| UTC | Beobachtung |
|---|---|
| 21:03:32.273 | connect_time von SPID 53 |
| 21:03:32.363 | Beginn der Transaktion 13578 |
| 21:03:33.400 | sleeping, open_transaction_count=1 |
| 21:04:02.002 | Letzte Stichprobe mit aktiver Transaktion |
| 21:04:02.922 | Nächste Anwendungsoperation erfolgreich |
| 21:04:03.101 | Erste Stichprobe mit open_transaction_count=0 |

![Transaktion nach Dispose](/images/lab68/03-transaction-after-dispose.svg)

*Abbildung 3. DMV-Stichproben; der Zustandswechsel liegt innerhalb des Abtastintervalls.*

In 27 Stichproben war die Transaktion aktiv (state 2), in den folgenden 14 nicht mehr vorhanden. SPID und connect_time blieben gleich. In dieser Konfiguration überdauerte die T-SQL-Transaktion Dispose und verschwand bei der Wiederverwendung der Verbindung. Hier wurden keine Daten geändert; die Blockierung untersuchte ich separat.

## 6. Experiment D – Blockierung nach Dispose

In `tempdb` erstelle ich eine Tabelle mit eindeutigem Namen und dem Anfangswert `V=0`. Beispiel für T-SQL in der Besitzer-Sitzung:

```sql
BEGIN TRANSACTION;
UPDATE dbo.Lab68_Test SET V = 1 WHERE Id = 1;
```

Nach Dispose führt eine zweite Sitzung über eine unabhängige Verbindung ohne Pooling folgende Abfrage aus:

```sql
SELECT V FROM dbo.Lab68_Test WITH (READCOMMITTEDLOCK)
WHERE Id = 1;
```

Der Hint erzwingt auch bei aktiviertem RCSI einen sperrenbasierten Lesezugriff. Im tatsächlichen Code wird der Tabellenname dynamisch generiert.

| Parameter | Besitzer | Beobachter |
|---|---|---|
| SPID | 60 | 59 |
| Session status | sleeping | running |
| Request status | NULL | suspended |
| Open transactions | 1 | 0 |
| Wait type | NULL | LCK_M_S |
| Blocking session ID | NULL | 60 |

Neun aufeinanderfolgende Stichproben zeigten diese Blockierungsbeziehung. Nach 10 Sekunden wartete der Lesezugriff des Beobachters weiterhin. Die Wiederverwendung von SPID 60 ergab `@@TRANCOUNT=0`, und der Beobachter las den ursprünglichen Wert 0. Damit sind das Zurückrollen der Änderung und das Ende der Blockierung belegt.

![Blockierungskette](/images/lab68/04-blocking-chain.svg)

*Abbildung 4. Darstellung des durch Messungen belegten Mechanismus.*

## 7. Extended Events – Zurücksetzen der Sitzung

Die Ereignisse `login`, `logout`, `rpc_completed` und `sql_batch_completed` erlaubten die Rekonstruktion des Ablaufs in der Besitzer-Sitzung:

| UTC | Ereignis |
|---|---|
| 21:13:50.678 | login, is_cached=false |
| 21:13:50.681 | SELECT @@SPID |
| 21:13:50.693 | BEGIN TRANSACTION + UPDATE |
| 21:13:50.698 | Dispose im Anwendungsprotokoll |
| 21:14:00.711 | logout, is_cached=true |
| 21:14:00.711 | rpc_completed: sp_reset_connection |
| 21:14:00.711 | login, is_cached=true |
| 21:14:00.712 | SELECT @@SPID, @@TRANCOUNT |
| 21:14:00.715 | Lesezugriff des Beobachters abgeschlossen (Anwendungsprotokoll) |

XE meldete für den Reset von SPID 60 eine Dauer von 281 µs und das Ergebnis OK. Der Ringpuffer meldete acht Ereignisse, droppedCount=0 und truncated=0. Der Beobachter lag außerhalb des XE-Filters; sein Abschluss ist im Anwendungsprotokoll belegt. Cached-Login- und Logout-Ereignisse bedeuten hier keinen neuen physischen Verbindungsaufbau.

Der Reset bei Wiederverwendung, das Verschwinden der Transaktion und der gelesene Wert 0 ergeben ein konsistentes Bild des Mechanismus. Beim vorherigen Dispose beobachteten wir keinen Reset.

## 8. Experiment E – Explizites Rollback

Die Kontrollvariante verwendet die Transaktions-API von SqlClient und führt vor der Freigabe der Verbindung ein explizites Rollback aus:

```csharp
await using var tx = (SqlTransaction)await owner.BeginTransactionAsync();
// UPDATE mit tx als SqlCommand.Transaction
await tx.RollbackAsync();
```

| Parameter | D – Blocking | E – Rollback |
|---|---|---|
| UPDATE | Ja | Ja |
| Explizites Rollback | Nein | Ja |
| Lesezugriff wartet nach 10 s | Ja | Nein |
| LCK_M_* in Stichproben | LCK_M_S | Keine |
| TRANCOUNT nach Wiederverwendung | 0 | 0 |
| Gelesener Wert | 0 | 0 |

Die ursprünglich gemeldeten Zeiten von 10014 und 10012 ms enthielten das bewusst eingeplante Beobachtungsfenster. Sie sind keine vergleichbaren isolierten SELECT-Laufzeiten. Der Messcode wurde korrigiert, ein erneuter Test dieser Korrektur steht jedoch noch aus. Die Kontrollvariante ändert sowohl die Art des Transaktionsbeginns als auch das explizite Rollback und isoliert daher nicht die jeweiligen Einzeleffekte.

## 9. Diagnose im Produktivbetrieb

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

Inaktive Sitzungen mit offenen Transaktionen lassen sich gezielt ermitteln:

```sql
SELECT session_id, host_name, program_name, login_name,
       open_transaction_count, last_request_end_time,
       DATEDIFF(SECOND, last_request_end_time, SYSDATETIME()) AS IdleSeconds
FROM sys.dm_exec_sessions
WHERE is_user_process = 1 AND status = N'sleeping'
  AND open_transaction_count > 0
ORDER BY IdleSeconds DESC;
```

Entsprechende DMV-Berechtigungen sind erforderlich (bei SQL Server 2022 in der Regel VIEW SERVER PERFORMANCE STATE). Das Auffinden einer solchen Sitzung ist kein automatischer Grund für KILL. Zuerst sollten Besitzer, Transaktionsalter, blockierte Ressourcen und mögliche Auswirkungen eines Rollbacks ermittelt werden.

Offene Transaktionen können Blockierungen verursachen, die Wiederverwendung von Transaktionsprotokollspeicher verzögern und in entsprechenden Isolationsszenarien Zeilenversionen festhalten. Lange Blockierungen können wiederum die Belegungsdauer von Verbindungen erhöhen und den Pool erschöpfen. Das Wachstum des Transaktionsprotokolls, des Version Store oder eine solche Kaskade habe ich in Lab 68 jedoch nicht gemessen.

## 10. Empfehlungen für .NET-Entwickler und DBA

Verbindungen möglichst spät öffnen und möglichst früh freigeben. Sie nicht während unabhängiger HTTP-Operationen belegt halten. Transaktionen bewusst verwalten: COMMIT bei Erfolg und ein geeignetes Rollback im Fehlerfall; dabei bevorzugt die Transaktions-APIs von EF Core oder ADO.NET einsetzen. Einen späteren Sitzungsreset nicht als Bereinigungsstrategie einplanen.

Eine Erhöhung von Max Pool Size kann aufgrund der Arbeitslast sinnvoll sein, korrigiert aber keinen fehlerhaften Verbindungslebenszyklus. Active/Ready/Pooled, Anzahl der Pools, Wartezeit beim Verbindungsbezug, Ausnahmen und Transaktionsdauer überwachen. Diese Werte mit DMVs und XE korrelieren. DbContext Pooling ersetzt nicht die Verwaltung des SqlClient-Verbindungspools.

![Drei Diagnoseperspektiven](/images/lab68/05-diagnostic-perspectives.svg)

*Abbildung 5. Diagnosemethodik – schematische Darstellung.*

## 11. Reproduktion

Quellcode: [SQLManiak Lab 68 – PR #146](https://github.com/marcinpytlik/SQLManiak/pull/146). In einem isolierten Labor mit Docker, .NET 10, PowerShell 7, sqlcmd und dotnet-counters:

```powershell
cd labs\68_ConnectionPoolExhaustion
$env:LAB_PASSWORD = Read-Host "SA-Kennwort" -MaskInput
docker compose up -d
# Vor dem Test auf die Betriebsbereitschaft von SQL Server warten.
.\Invoke-Lab68.ps1 -Counters -XE
# Ausgewählte Szenarien:
.\Invoke-Lab68.ps1 -Scenario exhaustion -Counters -XE
.\Invoke-Lab68.ps1 -Scenario blocking,rollback -XE
```

Das Skript speichert Anwendungsprotokolle, DMVs, XE, Leistungsindikatoren und Paketversionen in einem separaten Ergebnisverzeichnis. Anschließend `docker compose down` und `Remove-Item Env:\LAB_PASSWORD` ausführen. SA und TrustServerCertificate werden ausschließlich im Labor verwendet.

## 12. Einschränkungen und Fazit

Die Experimente liefen lokal mit einem kleinen Pool, einem bestimmten Provider und einem erzwungenen sperrenbasierten Lesezugriff. Stichproben sind keine kontinuierliche Aufzeichnung; die Beobachtungen lassen sich nicht automatisch auf alle Bibliotheksversionen und Transaktions-APIs übertragen. Es handelt sich um eine Untersuchung des Mechanismus, nicht um einen Durchsatzbenchmark.

Fünf Beobachtungen: Aufeinanderfolgende DbContexts können dieselbe physische Sitzung nutzen; sleeping bedeutet keine freie Verbindung; Pool-Erschöpfung muss keinen SQL-Request erzeugen; eine T-SQL-Transaktion kann Dispose überdauern; eine inaktive Sitzung kann andere Benutzer blockieren. In der untersuchten Konfiguration bestätigten XE den Reset bei Wiederverwendung und EventCounters die wiederhergestellte Verfügbarkeit des Pools.

Ein moderner DBA muss nicht nur verstehen, was in der Datenbank geschieht, sondern auch, was zwischen Anwendung und Datenbank passiert.

**SQLManiak – weniger Theorie, mehr Belege.**

## Quellen

- [Hannah Vernon – Connection Pool Exhaustion](https://www.sqlserverscience.com/troubleshooting/connection-pool-exhaustion/)
- [SQLManiak – Lab 68](https://github.com/marcinpytlik/SQLManiak/pull/146)
- [Microsoft Learn – SQL Server connection pooling](https://learn.microsoft.com/en-us/sql/connect/ado-net/sql-server-connection-pooling)
- [Microsoft Learn – dotnet-counters](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters)
