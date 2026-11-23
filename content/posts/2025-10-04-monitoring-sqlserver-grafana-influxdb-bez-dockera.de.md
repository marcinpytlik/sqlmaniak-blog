---
title: "SQL Server 2022 mit Grafana, InfluxDB und Telegraf überwachen (ohne Docker)"
date: "2025-10-04"
slug: "monitoring-sqlserver-grafana-influxdb-bez-dockera-de"
draft: false
description: "Schrittweise Windows-Einrichtung von InfluxDB 2.x, Telegraf und Grafana mit SQL-Server-Dashboards und Alarmen."
tags: ["Monitoring","Grafana","SQL Server"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/monitoring-sqlserver-grafana-influxdb-bez-dockera.png"

---

## Einleitung
Windows Server ohne Docker? InfluxDB 2.x, Telegraf und Grafana lassen sich trotzdem installieren und für SQL Server 2022 einsetzen.

## InfluxDB 2.x unter Windows
1. Als Dienst installieren und Organisation sowie Bucket konfigurieren (beispielsweise jeweils `Demo`).
2. Einen **API-Token** mit Lese- und Schreibrechten für den Bucket erzeugen.

## Telegraf-Inputs für SQL Server und Windows
Ausschnitte aus `telegraf.conf`:
```toml
[[outputs.influxdb_v2]]
  urls = ["http://localhost:8086"]
  token = "PASTE_TOKEN"
  organization = "Demo"
  bucket = "Demo"

[[inputs.sqlserver]]
  servers = ["Server=localhost;Port=1433;User Id=telegraf;Password=***;app name=Telegraf"]
  query_version = 2

[[inputs.win_perf_counters]]
  [[inputs.win_perf_counters.object]]
    ObjectName = "SQLServer:General Statistics"
    Counters = ["User Connections","Logins/sec"]
    Instances = ["*"]
```

## Grafana
- InfluxDB als Flux-Datenquelle hinzufügen.
- Dashboards importieren: *SQL Server Overview*, *Waits*, *Tempdb* und *IO latency*.
- Alarme einrichten: kein Backup innerhalb von 24 Stunden, `% Log Used > 80%` und `Tempdb Used > 70%`.

## Berechtigungen und Sicherheit
- Dem SQL-Login `telegraf` die Berechtigung `VIEW SERVER PERFORMANCE STATE` und Zugriff auf erforderliche Views/DMVs geben.
- Kennwörter im Windows Credential Manager oder einer separaten Umgebungsdatei speichern.

## Überprüfung
- Prüfen, ob Messwerte im Bucket eintreffen und Panels fehlerfrei angezeigt werden.
- Einen kontrollierten Test des Log-Auslastungsalarms auslösen und die Benachrichtigung prüfen.

> Bonus fürs Repository: `monitoring/telegraf.conf`, `grafana/dashboard.json` und eine `README.md` mit Installation und Fehlerbehebung ergänzen.
