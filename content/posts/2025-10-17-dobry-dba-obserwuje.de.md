---
title: "Ein guter DBA rät nicht — er beobachtet"
date: 2025-10-17
slug: dobry-dba-obserwuje
tags: [SQLServer, Monitoring, Grafana, InfluxDB, Telegraf, DevOps, DataPlatform]
draft: false
---

Jedes Diagramm erzählt eine Geschichte. CPU, I/O, Arbeitsspeicher und Abfragen zeigen, was auf dem Server tatsächlich geschieht. Ein guter DBA reagiert nicht nur auf einen Alarm — er versteht, *warum* er ausgelöst wurde.

Mein bevorzugter Stack ist **Telegraf + InfluxDB + Grafana**. Zusammen entsteht ein Cockpit: **SQLManiak Monitoring**. Kein Dashboard, das nur hübsch aussehen soll, sondern eine **Landkarte des Systemverständnisses**, auf der jede Metrik eine Bedeutung hat.

> „Wissen beginnt dort, wo das Raten endet.“

---

### Von der Reaktion zur Beobachtung

Die meisten Performanceprobleme entstehen nicht plötzlich. Sie entwickeln sich leise zwischen `BACKUP`- und `CHECKDB`-Läufen und einer weiteren zu langen `SELECT *`-Abfrage. Ohne Monitoring sehen wir nur das Ergebnis: einen roten Alarm, längere Antwortzeiten oder sinkende PLE-Werte.

Monitoring ist keine Magie. Es ist **Bewusstsein über die Zeit** — eine Ereignishistorie, die zeigt, wie der Server wirklich arbeitet. Wenn etwas schiefläuft, geht es nicht um Panik, sondern um *Verständnis*.

---

### Woraus mein Cockpit besteht

Jede Komponente erfüllt eine eigene Aufgabe:

- **Telegraf** sammelt Daten aus SQL Server, Windows, IIS und dem Netzwerk. Plugins wie `inputs.sqlserver`, `inputs.win_perf_counters`, `inputs.tail` (für IIS-Protokolle) und `inputs.ping` liefern ein umfassendes Systembild.

- **InfluxDB** speichert Zeitreihenmetriken. Jeder Messpunkt beschreibt einen Zeitpunkt: `cpu_usage`, `wait_stats`, `tempdb_free_space`, `connections_active`. Buckets und Aufbewahrungsregeln halten aktuelle und historische Informationen vor.

- **Grafana** visualisiert diese Informationen — ein Spiegel des Systemzustands. Dashboards zeigen Trends, Alarme erkennen Abweichungen vom Normalzustand. Es geht nicht um bunte Diagramme, sondern darum, auf einen Blick die nächste Entscheidung treffen zu können.

---

### Was das Dashboard zeigt

Mein Dashboard ist in Bereiche gegliedert:

1. **System** — CPU, RAM, I/O und Netzwerk. Der Rhythmus und Ressourcenverbrauch des Servers.
2. **SQL Server** — PLE, PAGEIOLATCH, THREADPOOL, tempdb-Auslastung und aktive Sitzungen. Hier zeigt SQL Server, wo es schmerzt.
3. **Storage und Protokolle** — Datenträgerlatenz, Schreiblatenz, IOPS und Transaktionsprotokollstatistiken. Hier endet die Theorie und beginnt die Physik.
4. **Query Insights** — die zehn wichtigsten Abfragen nach CPU-Zeit, logischen Lesezugriffen und Schreibvorgängen. Hier siehst du, was tatsächlich Rechenzeit verbraucht.
5. **Alarme und Anomalien** — Schwellenwerte und Trends, die ungewöhnliches Verhalten erkennen. Zuverlässigkeit beginnt damit, *Abweichungen vom Normalzustand* zu bemerken.

---

### Warum Performance Monitor allein nicht genügt

Die Diagramme in `perfmon.msc` zeigen, dass etwas passiert, aber nicht unbedingt *warum*. Mit Grafana kannst du Zusammenhänge vergleichen: CPU und Sitzungen, I/O und Abfragen, Arbeitsspeicher und tempdb. Erst das **Zusammenspiel der Diagramme** macht Beziehungen sichtbar, die einzelne Leistungsindikatoren nicht zeigen.

Du rätst nicht und gerätst nicht in Panik. Du schaust hin — und erkennst.

---

### Die Philosophie des Beobachtens

Ein DBA ist ein wenig wie ein Astrophysiker: Du kannst einen Stern nicht anhalten, aber verstehen, warum er heute anders leuchtet als gestern.

Auch SQL Server ist in diesem Bild ein lebender Organismus. Er hat Rhythmus, Gedächtnis, Eigenheiten und sein eigenes Reaktionstempo. Verständnis entsteht erst, wenn du nicht nur Fehler betrachtest, sondern nach ihren *Ursachen* suchst.

> „Monitoring ist kein Werkzeug. Es ist eine Denkweise.“

---

### Experiment

Installiere lokal:

```bash
choco install telegraf influxdb grafana
```

Konfiguriere:

```toml
[[outputs.influxdb_v2]]
  urls = ["http://localhost:8086"]
  token = "$INFLUX_TOKEN"
  organization = "Demo"
  bucket = "Monitoring"
```

Füge das Plugin hinzu:

```toml
[[inputs.sqlserver]]
  servers = ["Server=localhost;User ID=telegraf;Password=Secret;app name=SQLMonitor"]
```

Starte Grafana, füge InfluxDB als Datenquelle hinzu und importiere ein Dashboard. Der erste Blick überrascht immer: Plötzlich *beginnt der Server zu sprechen*.

---

Verständnis ist der Anfang von Kontrolle. Ein guter DBA rät nicht — er beobachtet. Deshalb bleiben seine Server ruhig, selbst wenn ringsherum alles in Flammen zu stehen scheint.
