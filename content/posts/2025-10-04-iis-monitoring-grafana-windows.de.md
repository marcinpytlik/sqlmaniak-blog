---
title: "IIS und Windows: schnelles Monitoring mit Grafana, Telegraf und InfluxDB"
date: "2025-10-04"
slug: "iis-monitoring-grafana-windows-de"
draft: false
description: "IIS-Metriken und Zugriffslogs mit Telegraf sammeln und über InfluxDB 2.x in Grafana visualisieren."
tags: ["IIS","Monitoring","Grafana"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/iis-monitoring-grafana-windows.png"

---

## Einleitung
IIS steht häufig vor einem SQL-Server-Backend. Hier ist eine kompakte Pipeline für Metriken und Logs in Grafana.

## Telegraf: Performance Counter
```toml
[[inputs.win_perf_counters]]
  [[inputs.win_perf_counters.object]]
    ObjectName = "Web Service"
    Counters = ["Current Connections","Get Requests/sec","Post Requests/sec"]
    Instances = ["_Total"]
```

## Telegraf: IIS-Logs (tail und grok)
```toml
[[inputs.tail]]
  files = ["C:/inetpub/logs/LogFiles/W3SVC1/u_ex*.log"]
  from_beginning = false
  data_format = "grok"
  grok_patterns = ['%{TIMESTAMP_ISO8601:time} %{IPORHOST:client} %{WORD:method} %{URIPATHPARAM:uri} %{NUMBER:status:int} %{NUMBER:sc_substatus:int} %{NUMBER:sc_win32_status:int} %{NUMBER:time_taken:int}']
```

## Grafana
- Panels: `HTTP 5xx`, `Average time_taken`, `Requests/sec`.
- Alarm, wenn die 5xx-Rate fünf Minuten lang über 1 % liegt.

## Praxistipp
Synchronisiere die Uhren per NTP; sonst wird die Korrelation von Logs und Metriken schwierig.
