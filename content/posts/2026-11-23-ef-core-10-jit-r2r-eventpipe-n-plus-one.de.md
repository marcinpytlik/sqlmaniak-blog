---
title: "EF Core aus DBA-Sicht: Kann JIT das N+1-Problem retten? .NET 10, ReadyToRun und EventPipe"
date: 2026-11-23T08:00:00+01:00
slug: "ef-core-10-jit-readytorun-eventpipe-n-plus-one"
description: "Fortsetzung des Labors mit EF Core 10 und SQL Server 2022: 640 Messungen beim Profiling von JIT, ReadyToRun, Composite und No-tiering. dotnet-counters, dotnet-trace, GC und Allokationen."
category: "Relationale Renaissance"
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

# EF Core aus DBA-Sicht: Kann JIT das N+1-Problem retten? .NET 10, ReadyToRun und EventPipe

**Wenn dieselbe EF-Core-Operation statt eines einzigen SQL-Befehls 101 Befehle ausführt: Kann eine schnellere .NET-Kompilierung diesen Unterschied ausgleichen?**

Diese Frage hat mich nach [meinem vorherigen Artikel über N+1, Include, Projection, SplitQuery und Query Store](/posts/ef-core-n-plus-one-include-projection-split-query-query-store/) weiter beschäftigt. Bei identischen Daten — **100 Bestellungen und 1.000 Bestellpositionen** — ermittelte ich Mediane von **119,83 ms für N+1** und **5,11 ms für Projection**. Auf der SQL-Server-Seite standen **1.103 gegenüber 14 logischen Lesevorgängen** pro Anforderung.

Diesmal gehe ich einen Schritt weiter, ohne die Abfragen oder das Datenbankschema zu verändern. Stattdessen ändere ich **die Veröffentlichungsart der .NET-10-Anwendung**, beobachte den Prozess mit `dotnet-counters` und `dotnet-trace` und vergleiche die Ergebnisse mit meinen früheren Query-Store-Messungen.

Es geht mir nicht darum, um jeden Preis einen Sieger zu küren. Ich möchte klären, **welche Aussagen CLR-Leistungsindikatoren tatsächlich ermöglichen, wenn SQL Server dieselbe Arbeit erledigt**.

**Quellcode, Skripte und Dokumentation: [WWSI_CSharp — Demo 67, EF Core Performance Lab](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).** Detaillierte Tabellen und methodische Einschränkungen stehen außerdem im [Abschlussbericht zu Experiment 03](https://github.com/marcinpytlik/WWSI_CSharp/blob/main/demonstracje/67_EfCorePerformanceLab/experiments/03_Compilation/FINAL-REPORT-2026-11-22.md).

## Zur Erinnerung: Was bleibt unverändert?

Die Anwendung verwendet **ASP.NET Core / .NET 10, EF Core 10 und SQL Server 2022 Developer** in Linux-Containern. Die Datenbank `EfPerformanceLab` enthält 100 Bestellungen mit jeweils 10 Positionen.

Alle vier Endpunkte liefern dieselben DTOs zurück. Ein automatisierter Test überprüft die Ergebnisgleichheit. Jede Implementierung verwendet `AsNoTracking()`.

| Strategie | Datenzugriff | SQL-Befehle pro Anforderung |
|---|---|---:|
| N+1 | Zunächst Bestellungen, danach ein eigener SELECT für die Positionen jeder Bestellung | **101** |
| Include | `Include()` und `AsSingleQuery()` | **1** |
| Projection | `Select()` direkt in DTOs | **1** |
| SplitQuery | `Include()` und `AsSplitQuery()` | **2** |

N+1 ist hier **ein absichtlich implementiertes Antipattern** und keine zufällige Folge von Lazy Loading. Dadurch kann ich das Problem reproduzieren, ohne auf eine bestimmte Konfiguration von Navigationseigenschaften angewiesen zu sein.

Aus DBA-Sicht zählt die Anzahl der Operationen, die **eine fachliche Anforderung** auslöst — nicht nur der Aufwand eines einzelnen SELECT.

## Vier Möglichkeiten, dieselbe Anwendung auszuführen

In einem separaten Veröffentlichungsexperiment habe ich vier Varianten vorbereitet. Alle verwenden **Release, linux-x64 und eine eigenständige Veröffentlichung (self-contained)**. Gerade für Composite ReadyToRun ist diese Voraussetzung wichtig.

| Modus | Veröffentlichungs-/Runtime-Konfiguration | Tiered Compilation |
|---|---|---|
| `jit` | `PublishReadyToRun=false` | Aktiviert |
| `r2r` | `PublishReadyToRun=true` | Aktiviert |
| `composite` | `PublishReadyToRunComposite=true` | Aktiviert |
| `no-tiering` | Veröffentlichung wie `jit`, `TieredCompilation=0` | Deaktiviert |

`no-tiering` ist keine zusätzliche Kompilierungstechnologie. Vielmehr ändere ich das Verhalten der Runtime: Ich deaktiviere die gestufte Kompilierung. Damit kann sich das Verhältnis zwischen Kompilierungsaufwand und Qualität des erzeugten Codes verändern.

Um solche Effekte besser zu unterscheiden, gab es zuvor die Phase **03B**: vier ausbalancierte Runden mit wechselnder Reihenfolge der Modi und jeweils 10 Wiederholungen pro Strategie. Daraus ergeben sich **4 Runden × 4 Modi × 4 Strategien × 10 Wiederholungen = 640 Anwendungsmesswerte**. In Phase **03C** wurden Kennzahlen für den gesamten Prozess erfasst (CPU, Allokationen, GC-Läufe). Im Mittelpunkt dieses Artikels steht Phase **03D** — ein separates Experiment mit EventPipe-Werkzeugen.

Die Unterscheidung ist wichtig: **Die 640 Messwerte aus 03B und die 640 aus 03D bilden unterschiedliche Datensätze**, die unter verschiedenen Bedingungen entstanden sind.

## Wie habe ich EventPipe an einen Prozess in Docker angebunden?

Die Anwendung läuft in einem Runtime-Image. Die Diagnosewerkzeuge befinden sich dagegen in **einem separaten Container namens `profiler`**, der auf .NET SDK 10 basiert.

Mit Docker Compose teilt der Profiler zwei Ressourcen mit der API:

- den PID-Namensraum (`pid: "service:api"`);
- das Volume `/tmp`, in dem .NET seinen Diagnosesocket bereitstellt.

So erkennt `dotnet-counters ps` den Anwendungsprozess. Die Werkzeuge können sich verbinden, ohne dass ich das SDK im Runtime-Image der API installieren muss.

Beispiele für Befehle innerhalb des Profiler-Containers:

~~~bash
/tools/dotnet-counters collect \
    --process-id 1 \
    --refresh-interval 1 \
    --format csv \
    --counters System.Runtime \
    --output /output/jit-counters.csv
~~~

~~~bash
/tools/dotnet-trace collect \
    --process-id 1 \
    --profile dotnet-common,dotnet-sampled-thread-time \
    --output /output/jit-trace.nettrace
~~~

**Ich starte die beiden Profiler nicht gleichzeitig.** Jedes Werkzeug erhält eine eigene Reihe von Anforderungen. Die Traces erfassen den Prozess **nach dem Start und dem Warm-up**. Sie messen weder den Kaltstart der CLR noch die gesamten anfänglichen JIT-Kosten.

In Phase 03D habe ich für jeden Modus **20 Wiederholungen aller vier Strategien** während einer `dotnet-counters`-Sitzung durchgeführt und anschließend weitere 20 Wiederholungen während einer `dotnet-trace`-Sitzung:

**4 Modi × 4 Strategien × 20 Wiederholungen × 2 Erfassungsarten = 640 gemessene EF-Core-Operationen.**

Vor jeder eigentlichen Messreihe bestätigte ein Test sowohl die zurückgegebenen Daten als auch die Anzahl der SQL-Befehle: **101 / 1 / 1 / 2**.

## Laufzeiten während des Profilings: N+1 fällt weiterhin deutlich auf

Die folgenden Tabellen zeigen den **Median der Dauer der eigentlichen EF-Core-Operation**, nicht die vollständige HTTP-Latenz und auch nicht die CPU-Zeit von SQL Server.

### Sitzung mit `dotnet-counters` — Median in ms

| Strategie | JIT | R2R | Composite R2R | Ohne Tiering |
|---|---:|---:|---:|---:|
| **N+1** | **135,13** | **177,27** | **136,99** | **169,22** |
| Include | 6,27 | 7,39 | 6,64 | 9,79 |
| Projection | **5,76** | 6,75 | 6,09 | 6,20 |
| SplitQuery | 6,46 | 6,67 | 6,55 | 7,71 |

### Sitzung mit `dotnet-trace` — Median in ms

| Strategie | JIT | R2R | Composite R2R | Ohne Tiering |
|---|---:|---:|---:|---:|
| **N+1** | **137,43** | **145,46** | **142,01** | **178,11** |
| Include | 8,00 | 7,35 | 8,51 | 11,06 |
| Projection | **6,05** | 6,66 | 6,89 | 7,48 |
| SplitQuery | 6,67 | **6,17** | 6,52 | 7,66 |

Die auffälligste Beobachtung betrifft nicht R2R. **Bei allen gemessenen Modi bleibt N+1 mehr als eine Größenordnung langsamer als die anderen Strategien.** In der JIT-Sitzung mit `dotnet-counters` betrug das Verhältnis der Mediane von N+1 und Projection ungefähr **23,5:1**.

Das bedeutet nicht, dass JIT grundsätzlich besser als ReadyToRun wäre. Es handelt sich um **lokale Mediane aus Profiling-Sitzungen, die in einer festen Reihenfolge durchgeführt wurden**. Das Profiling belastet den untersuchten Prozess zusätzlich; diese Phase war hinsichtlich der Reihenfolge nicht ausbalanciert.

Für Aussagen über die Wiederholbarkeit von Effekten der Kompilierungsmodi muss ich auf die separaten, ausbalancierten Runden **03B** zurückgreifen, statt einfach den kleinsten Wert aus den 03D-Tabellen auszuwählen.

## Was zeigen die System.Runtime-Leistungsindikatoren?

Neben den Medianen der Operationen habe ich Kennzahlen für **den gesamten API-Prozess** untersucht. Hier die Zusammenfassung der `dotnet-counters`-Sitzungen:

| Kennzahl | JIT | R2R | Composite | Ohne Tiering |
|---|---:|---:|---:|---:|
| Prozessallokationen, MB* | 124,4 | 123,0 | 124,0 | 125,3 |
| JIT-Zeit, s* | 3,04 | 2,92 | 2,86 | 0,04 |
| Per JIT kompilierte Methoden* | 3.752 | 3.278 | 2.808 | 63 |
| CPU-Zeit im User-Modus, s* | 4,84 | 5,16 | 4,86 | 3,05 |
| Median des Working Set, MB | 185,4 | 188,7 | 199,3 | 164,3 |
| Gen0-GC-Läufe* | 7 | 7 | 8 | 8 |

\* Die aus zeitlichen Leistungsindikator-Stichproben (`System.Runtime`, ungefähr im Sekundentakt) aggregierten Werte sind **Näherungswerte**. Ihre Interpretation hängt von der Semantik des jeweiligen Indikators ab. Sie beschreiben nicht einen einzelnen EF-Core-Aufruf.

Der Modus `no-tiering` meldete während der Erfassung wesentlich weniger JIT-Kompilierungsaktivität. Dennoch waren seine Medianlaufzeiten meistens höher als die der anderen Modi.

Das ist eine wichtige Warnung vor einem zu einfachen Schluss:

> Weniger Zeit für die JIT-Kompilierung bedeutet nicht zwangsläufig eine geringere Latenz einer Operation in einer bereits laufenden Anwendung.

Allerdings ist das **kein Nachweis für einen kausalen Zusammenhang**. Die Qualität des generierten Codes, der Prozesszustand, das Warm-up, die Testreihenfolge und der zusätzliche Aufwand des Profilings können das Ergebnis beeinflusst haben. Aus dieser Tabelle allein lässt sich keine allgemeingültige Empfehlung für oder gegen Tiered Compilation ableiten.

### Und was ist mit GC und Arbeitsspeicher?

Die näherungsweisen Gesamtallokationen des Prozesses lagen in diesen Sitzungen eng beieinander — bei etwa **123–125 MB**. Hier ist keine Veränderung um eine Größenordnung zu erkennen, die für sich genommen den Leistungsabstand zwischen N+1 und Projection erklären könnte.

**Das Working Set ist keine Allokationskennzahl.** Auch die Anzahl der Gen0-GC-Läufe beschreibt nicht unmittelbar die GC-Kosten eines bestimmten Endpunkts. Gemessen wird der ASP.NET-Core-Server einschließlich HTTP-Verarbeitung, Serialisierung, Bibliotheken und Runtime-Aktivität.

Um nachzuweisen, dass ein bestimmtes Zeitintervall durch GC oder JIT beansprucht wurde, müsste ich die Ereignisse und Aufrufstapel im betreffenden Zeitraum untersuchen, nicht nur aggregierte Leistungsindikatoren.

## Eine Falle im Experiment: Eine gültige Trace-Datei ist nicht unbedingt vollständig

Beim Automatisieren der Diagnostik trat ein Problem auf, das selbst ein gutes Beispiel für technische Fehlersuche ist.

In der ursprünglichen Serie `3b971dd5` verwendete ich zunächst diese Begrenzung:

~~~text
dotnet-trace --duration 150s
~~~

Die gesamte Anforderungsserie dauerte aber ungefähr **168–170 Sekunden**. Das Werkzeug speicherte eine `.nettrace`-Datei korrekt, beendete die Datenerfassung jedoch **vor dem Ende der Anforderungsserie**.

Welche Konsequenzen hat das?

Ich kann nicht die vollständige Geschichte von 80 Anforderungen einem Trace zuordnen, der nur einen Teil davon abdeckt. Ebenso wenig darf ich aus der größeren Composite-R2R-Trace-Datei — in der früheren Serie ungefähr **157 MB** — auf eine höhere CPU-Auslastung, einen größeren Speicherverbrauch oder höhere GC-Kosten schließen. Die Dateigröße hängt auch von der Anzahl und Art der aufgezeichneten Ereignisse ab.

Deshalb habe ich das Skript korrigiert: `dotnet-trace` läuft jetzt bis zum Ende der Anforderungsserie und erhält anschließend **Enter über ein Pseudoterminal und eine FIFO**. `dotnet-counters` wird entsprechend mit `q` sauber beendet. Außerdem musste ich für das Bash-Skript, das aus dem Repository unter Windows gebaut wird, **LF-Zeilenenden** erzwingen.

**Der neue Mechanismus bestand einen Integrationstest unter Docker Desktop (Lauf `b8e2a335`):**

- `PASS jit counters` — eine CSV-Datei mit **266.456 Byte** wurde gespeichert;
- `PASS jit trace` — eine `.nettrace`-Datei mit **26.108.814 Byte** wurde gespeichert;
- alle vier Strategien bestanden die Tests auf Ergebnisgleichheit.

Dieser Test **bestätigt das korrekte Beenden und Speichern der neuen Sitzung nach der Anforderungsserie**. Er ist noch keine unabhängige Analyse der vollständigen Ereigniszeitachse innerhalb der Trace-Datei.

## Warum darf ich nicht SQL-Zeit von EF-Core-Zeit abziehen?

Kehren wir zu den ursprünglichen Query-Store-Ergebnissen zurück:

| Strategie | Median der EF-Operation, ms | Durchschnittliche SQL-CPU pro Anforderung, ms | Logische Lesevorgänge pro Anforderung |
|---|---:|---:|---:|
| N+1 | 119,83 | 21,40 | 1.103 |
| Include | 6,01 | 1,95 | 14 |
| Projection | **5,11** | 2,73 | **14** |
| SplitQuery | 5,23 | **1,70** | 17 |

Es liegt nahe, von den 119,83 ms Median 21,40 ms abzuziehen und den Rest als „EF-Core-Overhead“ zu bezeichnen. Genau das wäre jedoch ein methodischer Fehler.

Erstens sind der **Median einer Operationsdauer** und die **durchschnittliche SQL-CPU-Zeit** statistisch nicht direkt vergleichbare Größen. Zweitens entspricht die CPU-Zeit von SQL Server nicht der Zeit, die der Client auf ein Ergebnis wartet. Drittens fallen auf Anwendungsseite weitere Kosten an: Materialisierung, Wartezeiten, Netzwerk-Roundtrips, Scheduling und die Erstellung von DTOs.

Deshalb brauchte ich **drei Perspektiven**:

1. `Stopwatch` innerhalb der API — wie lange die Operation dauert;
2. **Query Store** — welche Arbeit die SQL-Anweisungen im Datenbankmodul verursachen;
3. **EventPipe und CLR-Leistungsindikatoren** — was der gesamte Anwendungsprozess während der Anforderungsserie macht.

Keine dieser Perspektiven allein erklärt das Gesamtsystem.

## Wie lässt sich das Profiling reproduzieren?

Das Labor liegt im [Repository WWSI_CSharp, Demonstration 67](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).

Nach der Konfiguration von `.env` und dem Start des SQL-Server-Laborcontainers wechseln wir in das Verzeichnis von Demo 67:

~~~powershell
git clone https://github.com/marcinpytlik/WWSI_CSharp.git
cd WWSI_CSharp/demonstracje/67_EfCorePerformanceLab

Copy-Item env.template .env
# In .env ein eigenes starkes SQL_SA_PASSWORD festlegen.

docker compose up -d sql

./experiments/03_Compilation/Run-EventPipeDiagnostics.ps1 `
    -Modes jit `
    -Take 100 `
    -Repetitions 10 `
    -CaptureSeconds 300
~~~

Für alle Kompilierungsmodi:

~~~powershell
./experiments/03_Compilation/Run-EventPipeDiagnostics.ps1 `
    -Modes jit,r2r,composite,no-tiering `
    -Take 100 `
    -Repetitions 20 `
    -CaptureSeconds 300
~~~

Die Ergebnisse werden unter `experiments/03_Compilation/results/` gespeichert: CSV-Dateien mit Leistungsindikatoren, CSV-Dateien zu den einzelnen Anforderungen, `.nettrace`-Dateien, Protokolle und Manifeste.

Der Parameter `CaptureSeconds` ist jetzt **ein Richtwert**. Wird er überschritten, gibt das Skript eine Warnung aus, beendet die Datenerfassung jedoch nicht vor Abschluss aller Anforderungen.

**Diese Konfiguration darf nicht gegen einen produktiven SQL Server eingesetzt werden.** Die Demonstration verwendet lokale Container, synthetische Daten, ein vereinfachtes `sa`-Konto und einen gemeinsamen Diagnosenamensraum.

## Fazit: erst die Abfragen, dann der Compiler

Aus diesen Experimenten nehme ich fünf Beobachtungen mit.

**Erstens:** Das N+1-Problem dominiert bei allen untersuchten Runtime-Konfigurationen. Ein Compiler macht aus 101 SQL-Befehlen keinen einzigen.

**Zweitens:** Bei dieser Datenmenge liegen die Laufzeiten von Projection, Include und SplitQuery in einer ähnlichen Größenordnung. Sie unterscheiden sich aber in SQL-Struktur, Anzahl der Roundtrips und Aufwand für die Datenbank-Engine.

**Drittens:** Weniger JIT-Aktivität garantiert keine geringere Latenz. Kompilierungskosten und die Ausführungsgeschwindigkeit bereits kompilierten Codes sind unterschiedliche Aspekte.

**Viertens:** Prozessindikatoren und Query Store betrachten unterschiedliche Bereiche. Ich ordne weder alle API-Allokationen einer einzelnen EF-Core-Operation noch die SQL-CPU-Zeit der HTTP-Antwortdauer zu.

**Fünftens:** Dass ein Profiler eine Datei gespeichert hat, reicht nicht aus. Man muss zusätzlich überprüfen, ob sie **das gesamte untersuchte Zeitintervall** abdeckt.

Im vorherigen Artikel fragte ich, ob sich die Kompilierungsstrategie wesentlich auf die Dauer derselben Operation auswirken kann. Nach weiteren Messungen lautet meine Antwort: **Ein Einfluss ist möglich, erreichte in diesem Labor aber nicht annähernd das Ausmaß der Folgen einer N+1-Implementierung**. Gleichzeitig habe ich keine Grundlage dafür, einen Kompilierungsmodus allgemein zum schnellsten zu erklären.

**Bei der Optimierung von EF Core sollte die erste DBA-Frage nicht „Wie funktioniert JIT?“ lauten, sondern „Wie viele SQL-Abfragen erzeugt diese Operation tatsächlich — und was zeigt Query Store?“**

---

*Messreihe 03D: `3b971dd5`, 22. November 2026, 640 während des Profilings erfasste Operationsmessungen. Die Korrektur zum Beenden der EventPipe-Erfassung wurde separat im Lauf `b8e2a335` geprüft. Frühere Query-Store-Messungen: 10 Wiederholungen je Strategie, Lauf `fb6e09ce`. Die Ergebnisse stammen aus einem lokalen Labor und sind kein allgemeingültiger Benchmark für EF Core, SQL Server oder .NET-Kompilierungsmodi. Roh-Traces wurden nicht hinsichtlich Aufrufstapeln und Ereigniszeitachsen analysiert. Code und vollständiger Bericht: [Demo 67](https://github.com/marcinpytlik/WWSI_CSharp/tree/main/demonstracje/67_EfCorePerformanceLab).*
