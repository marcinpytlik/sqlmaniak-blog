---
title: "EF Core aus DBA-Sicht: 101 Abfragen gegen eine. Was zeigt der Query Store wirklich?"
date: 2026-11-22T12:00:00+01:00
slug: "ef-core-n-plus-one-include-projection-split-query-query-store"
description: "Ein kontrolliertes Experiment mit .NET 10, EF Core 10 und SQL Server 2022: N+1, Include, Projection und SplitQuery im Vergleich – Laufzeit, SQL-CPU, logische Lesevorgänge und die Frage nach JIT und AOT."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - EF Core
  - .NET 10
  - Query Store
  - N+1
  - Performance-Tuning
  - ORM
draft: true
---

# EF Core aus DBA-Sicht: 101 Abfragen gegen eine. Was zeigt der Query Store wirklich?

**Besteht das N+1-Problem lediglich aus einer zu hohen Anzahl von SQL-Anweisungen? Und wenn die Projektion auf DTOs aus Sicht der Anwendung am schnellsten ist, benötigt sie dann zwangsläufig die wenigste CPU-Zeit auf dem SQL Server?**

Statt diese Fragen aus dem Bauch heraus zu beantworten, habe ich ein reproduzierbares Labor mit **.NET 10, EF Core 10 und SQL Server 2022** aufgebaut. Ich habe vier Varianten zum Abrufen derselben Daten implementiert, ihre Ausführungszeiten in der Anwendung gemessen und anschließend die Differenzen der Query-Store-Zähler verglichen.

Die Ergebnisse zeigen zweierlei: N+1 verursacht messbare Kosten. Aber **die kürzeste Anwendungszeit bedeutet nicht zwangsläufig die geringste Belastung des Datenbankmoduls**.

Quellcode, Container und fertige Skripte:

**[WWSI_CSharp – Demonstration 67: EF Core Performance Lab](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab)**

## Laborumgebung und Umfang des Vergleichs

Performancemessungen sind nur im Kontext der verwendeten Hardware sinnvoll. In meinem [früheren Artikel über JIT, ReadyToRun und Native AOT](https://sqlmaniak.blog/posts/dotnet10-efcore10-sqlserver-startup-jit-r2r-native-aot/) habe ich folgende Hard- und Softwarekonfiguration dokumentiert:

| Komponente | Im früheren Labor dokumentierte Konfiguration |
|---|---|
| Hostbetriebssystem | Microsoft Windows 11 Pro, Version 10.0.26300 (Build 26300), x64 |
| Prozessor | Intel Core i5-1035G1 @ 1,00 GHz |
| Physische Kerne / logische Prozessoren | 4 / 8 |
| Arbeitsspeicher des Hosts | 7,81 GiB |
| .NET SDK | 10.0.403 |
| .NET / EF Core (früherer Test) | 10.0.14 / 10.0.14 |
| PowerShell (früherer Test) | 7.6.9 |
| Docker Client / Engine (früherer Test) | 29.9.2 / 29.9.2 |
| Containerumgebung (früherer Test) | Linux, 8 CPUs; etwa 3,73 GiB von `docker info` gemeldeter Speicher |

**Beide Experimente habe ich auf demselben physischen Rechner mit demselben Prozessor, Arbeitsspeicher und Betriebssystem durchgeführt.** Diese Hardwaredaten sind für beide Labore bestätigt. Die Versionen der Werkzeuge und die Ressourcen einzelner Container sind dagegen eigenständige Parameter; ohne erneute Prüfung gehe ich nicht davon aus, dass sie unverändert geblieben sind.

Für das **EF Core Performance Lab 67** ist folgende Konfiguration im [Repository der Demonstration](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab) nachvollziehbar:

| Komponente | Konfiguration von Demonstration 67 |
|---|---|
| Anwendung | ASP.NET Core / .NET 10, EF Core 10, API wird in Docker gebaut |
| Datenbankmodul | SQL Server 2022 Developer, Linux-Container |
| SQL-Server-Image | `mcr.microsoft.com/mssql/server:2022-latest` |
| SQL-Endpunkt auf dem Host | `127.0.0.1:14367` |
| API-Endpunkt auf dem Host | `127.0.0.1:5087` |
| Datenbank | `EfPerformanceLab` |
| Testdaten | 100 Bestellungen und 1.000 Positionen (10 pro Bestellung) |
| Query Store | `READ_WRITE`, `QUERY_CAPTURE_MODE = ALL` |
| Testserie | 10 Aufrufe pro Strategie, getrennte BEFORE/AFTER-Snapshots |
| Kennung des Durchlaufs | `fb6e09ce`, 22. November 2026 |

Im früheren Experiment lief SQL Server in einem **anderen Container**, `sql2022-startuplab`, auf Port **14333**. Für diesen Container habe ich **SQL Server 2022 RTM-CU27, 16.0.4295.3**, sowie eine Speicherbegrenzung von **4 GiB** nachgewiesen. **Diese beiden Angaben übertrage ich nicht ungeprüft auf Demonstration 67**: Das Image-Tag `2022-latest` ist veränderlich, und die Compose-Datei von Demonstration 67 legt keine Speichergrenze für SQL Server fest.

Für eine bessere Reproduzierbarkeit kann ich die tatsächliche Konfiguration des laufenden Containers von Demonstration 67 mit folgenden Befehlen erfassen:

```powershell
docker compose exec -T sql bash -c 'export SQLCMDPASSWORD="$MSSQL_SA_PASSWORD"; /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -d master -h -1 -W -Q "SET NOCOUNT ON; SELECT @@VERSION;"'
docker compose ps
docker version
docker info
```

Die identische Hardware erleichtert die Einordnung beider Experimente; die Konfiguration des SQL-Containers muss dennoch separat dokumentiert werden.

## Gleiche Daten, vier Strategien

Meine Testdatenbank enthält 100 Bestellungen mit jeweils 10 Positionen, also **100 Datensätze in Orders und 1.000 in OrderItems**. Jeder Endpunkt liefert dieselbe DTO-Struktur, dieselben Datensätze und dieselbe Reihenfolge der Elemente.

| Strategie | Vorgehensweise | SQL-Anweisungen pro Anfrage |
|---|---|---:|
| **N+1** | Ein SELECT für die Bestellungen, anschließend ein SELECT je Bestellung in einer Schleife | **101** |
| **Include** | `Include(x => x.Items)` + `AsSingleQuery()` | **1** |
| **Projection** | `Select()` direkt auf DTOs + `AsSingleQuery()` | **1** |
| **SplitQuery** | `Include(x => x.Items)` + `AsSplitQuery()` | **2** |

Alle Varianten verwenden `AsNoTracking()`. Das N+1-Muster setze ich absichtlich mit einer expliziten Schleife um, also ohne Lazy-Loading-Proxies. So ist der Effekt eindeutig nachvollziehbar: Zunächst werden alle übergeordneten Datensätze abgerufen, danach ihre untergeordneten Datensätze einzeln.

Eine vereinfachte Fassung dieses Antimusters:

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

    // DTO für die Bestellung und ihre Positionen erstellen.
}
```

**Das ist keine Empfehlung für den Produktivbetrieb.** Der Code ist bewusst ineffizient, damit ich den Aufwand messen kann.

Zum Vergleich ruft `Include` die zugehörigen Daten mit einer einzigen SQL-Anweisung ab:

```csharp
var orders = await db.Orders
    .AsNoTracking()
    .AsSingleQuery()
    .OrderBy(o => o.Id)
    .Take(100)
    .Include(o => o.Items)
    .ToListAsync();
```

Bei der Projektion werden die Daten direkt in DTOs übertragen. `AsSplitQuery()` teilt den Abruf der Bestellungen und ihrer einen Collection in zwei SQL-Anweisungen auf. Im vollständigen Demonstrationscode liefern alle Varianten **denselben Antwortvertrag**.

## Wie ich gemessen habe, ohne unzusammenhängende Zahlen zu vergleichen

Zuerst habe ich die Korrektheit der Daten überprüft und die SQL-Anweisungen mit `DbCommandInterceptor` gezählt. Erst danach begann die Performancemessung.

Für den abschließenden automatisierten Durchlauf verwendete ich:

- **10 Wiederholungen pro Strategie**, insgesamt also 40 Messungen der EF-Core-Operationen;
- einen Warm-up vor den eigentlichen Messreihen;
- separate Messreihen für N+1, Include, Projection und SplitQuery;
- für jede Reihe einen Query-Store-Snapshot **BEFORE**, den Benchmark und einen Snapshot **AFTER**;
- eine Kontrolle, ob Query Store die erwartete Anzahl der SQL-Ausführungen erfasst hat.

Der letzte Punkt ist entscheidend. Frühere Query-Store-Daten enthielten beispielsweise 4.271 Ausführungen einer Anweisung zum Abrufen der Bestellpositionen. Diese stammten jedoch nicht aus einem einzigen kontrollierten Messintervall. Solche historischen Summen **dürfen nicht** direkt mit zehn Aufrufen eines anderen API-Endpunkts verglichen werden.

Bei der Entwicklung der Snapshots stellte ich fest, dass ich die Anweisungen in dieser Umgebung anhand der von Query Store bereitgestellten Abfragetexte nicht zuverlässig über `TagWith()`-Kommentare filtern konnte. Die Suche nach `EFPLAB:` ergab vor dem Test keinen Treffer und danach genau einen: die Diagnoseabfrage selbst, in der der Marker als Zeichenfolgenliteral vorkam. Warum die Kommentare nicht in der erwarteten Form verfügbar waren, habe ich nicht abschließend geklärt. Stattdessen identifizierte ich charakteristische Bestandteile des generierten SQL und maß jede Strategie separat.

Für DBAs ist das eine wichtige Erinnerung: **Bevor ich Diagnosezähler vergleiche, muss ich sicherstellen, dass sie dieselbe Last und denselben Messzeitraum abdecken**.

## EF-Core-Ergebnisse: 119,83 ms gegenüber 5,11 ms

Im kontrollierten Durchlauf erhielt ich folgende Medianwerte der Operationen auf Anwendungsseite:

| Strategie | Median der EF-Core-Zeit | SQL-Anweisungen |
|---|---:|---:|
| N+1 | **119,83 ms** | 101 |
| Include | **6,01 ms** | 1 |
| Projection | **5,11 ms** | 1 |
| SplitQuery | **5,23 ms** | 2 |

In dieser konkreten Messreihe war der Median:

- bei Include etwa **19,9-mal kürzer** als bei N+1;
- bei Projection etwa **23,5-mal kürzer**;
- bei SplitQuery etwa **22,9-mal kürzer**.

Ist Projection damit immer die beste Lösung? **Nein.** Die Unterschiede zwischen den drei schnelleren Varianten sind klein. Für eine belastbare Bewertung benötige ich mehr Wiederholungen, unterschiedliche Datenvolumina und eine Analyse der Ausführungspläne.

Die `Stopwatch` erfasste die EF-Core-Operation bis zur Erstellung der Ergebnisobjekte. Die vollständige HTTP-Übertragung und die JSON-Serialisierung waren **nicht** Bestandteil der Messung.

## Query Store: Was sieht SQL Server?

Hier wird das Experiment besonders interessant.

Die folgenden Zahlen sind die **durchschnittlichen Kosten des SQL-Server-Datenbankmoduls pro API-Anfrage**, berechnet aus den Differenzen der Query-Store-Zähler:

| Strategie | SQL-CPU / Anfrage | Summe SQL-Duration / Anfrage | Logische Lesevorgänge / Anfrage |
|---|---:|---:|---:|
| N+1 | **21,40 ms** | 21,43 ms | **1.103** |
| Include | **1,95 ms** | 1,95 ms | **14** |
| Projection | **2,73 ms** | 2,73 ms | **14** |
| SplitQuery | **1,70 ms** | 1,70 ms | **17** |

Bei N+1 habe ich **1.103 logische Lesevorgänge (logical reads)** gemessen, bei Include und Projection dagegen jeweils nur **14**. Das entspricht einer Reduzierung um etwa **98,7 %**.

Eine frühere, unabhängig isolierte N+1-Messreihe bestätigte denselben Effekt: **1.000 Ausführungen** des SELECT auf OrderItems und **10 Ausführungen** des SELECT auf Orders. Zusammen ergaben sie **11.030 logische Lesevorgänge** für zehn Anfragen, also erneut 1.103 pro Anfrage.

Dabei handelt es sich **nicht um physische Datenträgerzugriffe**. Logische Lesevorgänge beschreiben Seitenzugriffe innerhalb des SQL-Server-Moduls, auch wenn die Seiten bereits im Buffer Pool vorhanden sind.

### 101 günstige Abfragen können teurer sein als eine größere

Ein einzelner Abruf der Positionen einer Bestellung ist kostengünstig. Das N+1-Muster wiederholt diesen Aufwand jedoch und erhöht gleichzeitig die Anzahl der Aufrufe zwischen Anwendung und SQL Server.

Daraus folgt nicht, dass ein SELECT mit JOIN immer schneller wäre als eine Suche über einen indizierten Fremdschlüssel. Entscheidend sind **die Gesamtkosten eines fachlichen Vorgangs**, nicht die isolierten Kosten einer einzelnen SQL-Anweisung.

Für einen DBA ist diese Perspektive wichtig: Auch eine Abfrage mit einer winzigen durchschnittlichen Laufzeit kann ein erhebliches Performanceproblem verursachen, wenn sie hunderttausendfach ausgeführt wird.

## Das Paradox: Schnellste EF-Core-Zeit, aber nicht die geringste SQL-CPU

Ich habe außerdem die drei schnelleren Varianten verglichen:

| Kennzahl | Include | Projection | SplitQuery |
|---|---:|---:|---:|
| Median EF Core | 6,01 ms | **5,11 ms** | 5,23 ms |
| SQL-CPU | 1,95 ms | 2,73 ms | **1,70 ms** |
| Logische Lesevorgänge | **14** | **14** | 17 |
| SQL-Anweisungen | **1** | **1** | 2 |

**Projection erreichte den kürzesten Median auf Anwendungsseite, benötigte unter diesen drei Varianten aber die meiste durchschnittliche SQL-CPU-Zeit.** SplitQuery beanspruchte am wenigsten durchschnittliche SQL-CPU, obwohl zwei Anweisungen ausgeführt wurden und mehr logische Lesevorgänge anfielen.

Das ist kein Widerspruch. In meinem Experiment habe ich verschiedene Bestandteile des Vorgangs gemessen:

- SQL Server führt den Ausführungsplan aus und liefert Datensätze zurück;
- EF Core materialisiert Entitäten oder erstellt DTOs;
- die Anwendung bereitet die Antwortobjekte auf;
- zusätzliche Round-Trips beeinflussen die Laufzeit, sind aber nicht mit der CPU-Zeit des Datenbankmoduls gleichzusetzen.

Außerdem vergleiche ich **einen Median der Anwendungszeit** mit **einer durchschnittlichen Summe der SQL-CPU-Zeit pro Anfrage**. Einfach 2,73 ms SQL-CPU von 5,11 ms Anwendungszeit abzuziehen und das Ergebnis als „EF-Core-Overhead“ zu bezeichnen, wäre methodisch falsch.

SplitQuery erwies sich als konkurrenzfähig. Das ist aber kein Grund, `AsSplitQuery()` grundsätzlich zu aktivieren: Bei mehreren Collections kann es die Vervielfachung von Zeilen durch JOINs reduzieren, erfordert dafür jedoch zusätzliche SQL-Anweisungen.

## So lässt sich das Experiment reproduzieren

Quellcode, Docker-Konfiguration, SQL-Skripte und eine vollständige Anleitung für Studierende stehen hier:

[**EF Core Performance Lab 67 – Vollständige Demonstration**](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab)

Voraussetzungen: Docker Desktop, PowerShell 7 und Git. Ein lokal installiertes .NET SDK oder SSMS ist nicht zwingend erforderlich.

```powershell
git clone https://github.com/marcinpytlik/WWSI_CSharp.git
cd WWSI_CSharp/demonstracje/67_EfCorePerformanceLab

Copy-Item env.template .env
# Ein eigenes starkes SQL_SA_PASSWORD in .env setzen.

docker compose up -d --build
Invoke-RestMethod http://localhost:5087/health
```

Nach der Initialisierung der Datenbank durch die API muss Query Store **ausschließlich in der Labordatenbank** für die vollständige Erfassung konfiguriert werden:

```sql
ALTER DATABASE EfPerformanceLab
SET QUERY_STORE (
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = ALL
);
```

Danach prüfe ich die korrekten Ergebnisse und starte den vollständigen Vergleich:

```powershell
./scripts/Test-Lab.ps1 -Take 100

./scripts/Run-All-Benchmark.ps1 -Take 100 -Repetitions 10
```

Das Skript führt vier isolierte Testreihen aus und erstellt eine gemeinsame Tabelle mit Anwendungszeit, SQL-CPU und logischen Lesevorgängen. Außerdem speichert es zwei CSV-Dateien mit einer Durchlaufkennung: eine Zusammenfassung und die einzelnen Messwerte.

**Dieses Experiment gehört nicht auf eine Produktionsdatenbank.** Die Demonstration nutzt bewusst eine vereinfachte `sa`-Konfiguration, festgelegte Testdaten und die automatische Schemaerstellung. Die README-Datei im Repository enthält die vollständige Anleitung und Hinweise zur Fehlersuche.

## Und was ist mit JIT, ReadyToRun und Native AOT?

Genau das ist die nächste Forschungsfrage, die sich aus den Ergebnissen ergibt.

Wenn SQL Server für eine N+1-Anfrage im Durchschnitt etwa 21,40 ms CPU benötigte, die EF-Core-Operation aber einen Median von 119,83 ms erreichte, **was passiert außerhalb des Datenbankmoduls?** Welchen Anteil haben die Ausführung des Anwendungscodes, die Materialisierung, die Kommunikation mit SQL Server, Speicherallokationen und Garbage Collection?

Kann die Art der .NET-Kompilierung daran etwas ändern?

Dafür benötige ich ein separates Experiment, bei dem Datenmodell und SQL-Workload gleich bleiben, aber die Veröffentlichungsart der Anwendung variiert:

1. CoreCLR mit JIT;
2. ReadyToRun;
3. Composite ReadyToRun;
4. eine Variante mit deaktivierter Tiered Compilation;
5. Native AOT – sofern ich die Anwendung mit den Einschränkungen dieses Modus kompatibel machen kann.

Native AOT ist kein universeller Schalter, der mit jeder EF-Core-Konfiguration funktioniert. Ein schnellerer Anwendungsstart bedeutet auch nicht automatisch geringere SQL-Ausführungskosten.

**Für Demonstration 67 liegen mir noch keine Vergleichsmessungen zwischen JIT und AOT vor.** Ich habe aber eine belastbare Ausgangsbasis für den nächsten Versuch.

Eines ist bereits klar: Eine andere Kompilierung der Anwendung verwandelt 101 SQL-Aufrufe nicht von selbst in einen einzigen.

## Fazit

Aus diesem Labor nehme ich vier praktische Erkenntnisse mit:

1. **Ich sollte den gesamten fachlichen Vorgang optimieren und nicht nur einen einzelnen SELECT.** N+1 kann mit vermeintlich günstigen Anweisungen tausende logische Lesevorgänge und zahlreiche Round-Trips verursachen.
2. **Die Strategie darf nicht allein anhand des EF-Core-Medians gewählt werden.** Auch SQL-CPU, Ausführungsanzahl und logische Lesevorgänge sind wichtig.
3. **Die Qualität der Messung ist genauso wichtig wie die Optimierung.** BEFORE/AFTER-Snapshots und die Überprüfung der Ausführungsanzahl verhindern Vergleiche mit unzusammenhängenden historischen Query-Store-Daten.
4. **Es gibt keinen universellen Sieger.** Projection, Include und SplitQuery haben unterschiedliche Vor- und Nachteile. Die Entscheidung muss vom Datenmodell, der Workload und reproduzierbaren Messungen abhängen.

Welche Variante hat also gewonnen? In meinem Szenario hatte Projection den kürzesten Median der EF-Core-Zeit, SplitQuery die geringste durchschnittliche SQL-CPU und N+1 mit Abstand die höchsten Gesamtkosten.

Die Frage, die mich am meisten interessiert, ist jedoch noch offen:

**Verändern JIT, ReadyToRun oder Native AOT die Laufzeit derselben Operation spürbar, wenn SQL Server exakt dieselbe Arbeit ausführt?**

Das wird das Thema der nächsten Laborreihe.

---

*Alle Performanceergebnisse beziehen sich auf den kontrollierten Durchlauf `fb6e09ce` von Demonstration 67 am 22. November 2026. Beide Experimente wurden auf demselben physischen Rechner durchgeführt; die genaue SQL-Server-CU-Version und die Speicherbegrenzung des Containers von Demonstration 67 wurden nicht gesondert dokumentiert. Die Ergebnisse sind kein allgemeingültiger Benchmark für EF Core oder SQL Server. Quellcode und Methodik: [WWSI_CSharp](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).*
