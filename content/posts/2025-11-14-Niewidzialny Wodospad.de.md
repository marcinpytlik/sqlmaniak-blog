---
title: '"Der unsichtbare Wasserfall" — I/O-Contention in SQL Server überwachen und beheben'
date: 2025-11-14
tags:
  - SQL Server
  - SQL Server 2022
  - Monitoring
  - Performance
  - I/O
categories:
  - SQLManiak
draft: false
---

# Der unsichtbare Wasserfall — I/O-Contention in SQL Server überwachen und beheben

Unter der Oberfläche von SQL Server läuft eine faszinierende Choreografie von Hintergrundprozessen ab, die die Performance bestimmen. Obwohl Checkpoint, Lazy Writer und Log Flush unterschiedliche Aufgaben erfüllen, konkurrieren sie um eine entscheidende Ressource: das I/O-Subsystem, das über die I/O-Scheduling-Mechanismen von SQL Server verwaltet wird.

Wer ihre Wechselwirkungen versteht, kann diese unsichtbare Konkurrenz mithilfe von DMVs und Extended Events (XE) sichtbar machen.

## Der Schlüssel: synchrones und asynchrones I/O

Um den „Wasserfall“ zu verstehen, müssen wir zwei Arten von Schreib-I/O unterscheiden:

**Synchrones I/O (kritisch):** Vor allem Log Flush, verbunden mit dem Wait `WRITELOG`. Eine Benutzersitzung, die `COMMIT` ausführt, muss unter Umständen warten, bis ihre Logeinträge dauerhaft geschrieben wurden. Das ähnelt einem Telefonat: Man wartet auf eine Antwort.

**Asynchrones I/O (Hintergrund):** Checkpoint und Lazy Writer können Schreibvorgänge im Hintergrund auslösen. Die Benutzersitzung wartet nicht unbedingt auf jeden einzelnen Abschluss. Das ist wie eine E-Mail: Die Zustellung erfolgt im Hintergrund.

Das Wasserfallproblem entsteht, wenn intensive Hintergrund-I/O, etwa Checkpoint-Schreibvorgänge, das Storage-Subsystem sättigt. Kritische Log Flushes leiden dann möglicherweise unter höheren Latenzen, weil sie dieselben Storage-Ressourcen nutzen.

## Was sollten wir überwachen?

Die Komponenten einzeln zu überwachen reicht nicht aus. Entscheidend ist die gemeinsame Beobachtung.

### 1. Checkpoint

Schreibt Dirty Pages aus Datendateien (MDF/NDF) und hilft, den Recovery-Aufwand zu begrenzen.

**Überwachung:** `sys.dm_db_log_stats` (unter anderem `log_bytes_to_checkpoint`) sowie das Extended Event `checkpoint_end`.

**Achtung:** Intensive Checkpoints können I/O sättigen und andere Operationen beeinträchtigen, möglicherweise auch Logschreibvorgänge.

### 2. Lazy Writer

Bei Speicherdruck im Buffer Pool hilft Lazy Writer, Puffer freizugeben, schreibt bei Bedarf Dirty Pages und gibt saubere Puffer frei.

**Überwachung:** Performance Counter `Lazy writes/sec` des Buffer Managers über `sys.dm_os_performance_counters`.

**Achtung:** Hohe Aktivität deutet auf Memory Pressure und zusätzliche Hintergrundschreibvorgänge hin.

### 3. Log Flush (Transaktionslog-Schreibvorgänge)

Ein kritischer Bestandteil von `INSERT`-, `UPDATE`- und `DELETE`-Transaktionen. Ein `COMMIT`, das Log-Dauerhaftigkeit benötigt, wartet auf den entsprechenden Flush.

**Überwachung:** `sys.dm_io_virtual_file_stats` für die LDF-Schreiblatenz und `wait_info` XE für `WRITELOG`.

**Achtung:** Hohe `WRITELOG`-Latenzen bremsen Transaktionsänderungen unmittelbar.

### 4. I/O-Scheduling und Wait Statistics

Waits bilden die Ressourcenkonkurrenz ab.

**Überwachung:** `sys.dm_os_wait_stats` für aggregierte Werte und `wait_info` XE für aktuelle Ereignisse.

**Achtung:** `WRITELOG`, `PAGEIOLATCH_SH`/`EX`/`UP` und `ASYNC_IO_COMPLETION`. Jeder Wait muss im Kontext interpretiert werden; sie bedeuten nicht automatisch denselben Engpass.

## Warum „der unsichtbare Wasserfall“?

Ein Prozess kann eine Kaskade auslösen:

1. Eine große Datenänderung erzeugt Tausende Dirty Pages.
2. Ein Checkpoint schreibt diese Seiten mit umfangreicher Hintergrund-I/O.
3. Das Storage-Subsystem gerät unter Druck.
4. Andere Transaktionen führen `COMMIT` aus und benötigen Log Flushes.
5. Die Log-Flush-Latenz steigt, wenn gemeinsame Storage-Ressourcen gesättigt sind.
6. Besteht zusätzlich Speicherdruck, erzeugt Lazy Writer weitere Schreibvorgänge.

## Weitere häufige Auslöser

**Index Rebuild:** Verursacht umfangreiche Lesezugriffe auf den alten Index, Schreibzugriffe auf den neuen Index und Transaktionslogaktivität.

**Full-/Differential-Backup:** Erzeugt große Datenlesevorgänge, die mit Benutzerabfragen konkurrieren können, etwa bei `PAGEIOLATCH_SH`.

**Autogrowth:** Eine plötzliche Vergrößerung von MDF- oder LDF-Dateien kann Operationen verzögern und ähnliche Symptome verursachen.

## Wie demonstrieren wir das?

**Last:** Erzeuge in einer Sitzung eine umfangreiche `INSERT`-/`UPDATE`-Last. Führe gleichzeitig in einer zweiten Sitzung kleine Transaktionen mit häufigem Commit aus.

**Extended Events:** Erfasse `checkpoint_end`, `log_flush_complete` und `wait_info`, gefiltert auf `WRITELOG` und relevante `PAGEIOLATCH`-Waits.

**Analyse:** Vergleiche Checkpoint-Aktivität und Log-Flush-Zeiten mit Spitzen der `WRITELOG`-Waits. Beachte, dass `checkpoint_end` das Ende und nicht den Beginn eines Checkpoints markiert.

## Tiefere Analyse: Welche Abfragen leiden? (Query Store)

Sobald ein Problem wie hohe `WRITELOG`-Waits feststeht, untersuche die betroffene Workload:

1. Öffne Query Store in SQL Server Management Studio.
2. Wähle **Top Resource Consuming Queries**.
3. Ändere die Metrik von CPU auf **Total Wait Time**, sofern verfügbar.
4. Sortiere die Abfragen und prüfe, welche `UPDATE`- oder `INSERT`-Operationen besonders lange warten.

So wird der Zusammenhang zwischen Storage-Druck und den betroffenen Abfragen sichtbar.

## 🎯 Wie lässt sich das Problem beheben oder entschärfen?

### 1. Checkpoint: Indirect Checkpoint

Indirect Checkpoint ist in modernen SQL-Server-Versionen für neue Datenbanken standardmäßig aktiviert und verwendet `TARGET_RECOVERY_TIME`.

**Wirkung:** Statt gelegentlicher großer Schreibspitzen versucht die Engine, Checkpoint-I/O gleichmäßiger zu verteilen. Das kann die Gefahr gesättigter Storage-Warteschlangen reduzieren.

**Maßnahme:** Überprüfe `TARGET_RECOVERY_TIME` (beispielsweise 60 Sekunden) und validiere das Verhalten unter der tatsächlichen Last.

### 2. Log Flush: I/O-Trennung

**Wirkung:** LDF- und MDF-/NDF-Dateien auf tatsächlich getrennten Storage-Ressourcen können die Konkurrenz zwischen Checkpoint-Schreibvorgängen und Log Flushes reduzieren. Unterschiedliche Laufwerksbuchstaben garantieren keine physische Trennung.

**Maßnahme:** Lege Transaktionslogs auf schnellen Speicher mit geringer Latenz, möglichst getrennt von intensiver Datendatei-I/O.

### 3. Lazy Writer: Memory Pressure

Übermäßige Lazy-Writer-Aktivität ist meist ein Symptom von Speicherdruck.

**Wirkung:** Weniger Speicherdruck bedeutet weniger aggressive Hintergrundschreibvorgänge.

**Maßnahme:** Prüfe die RAM-Kapazität und optimiere Abfragen oder Indizes, die unnötige Scans und Speicherverbrauch verursachen.

## Dashboard (zum Beispiel Grafana)

Visualisiere diese Metriken gemeinsam:

- Log-Flush-Latenz und `WRITELOG`-Waits.
- Schreiblatenz der Datendateien aus `sys.dm_io_virtual_file_stats`.
- Anzahl und Dauer der Checkpoints aus `checkpoint_end` XE.
- Lazy-Writer-Aktivität (`Lazy writes/sec`).
- Wichtige Wait Statistics.

Der Nutzen entsteht durch die Korrelation der Signale, nicht durch die isolierte Betrachtung einer einzelnen Metrik.
