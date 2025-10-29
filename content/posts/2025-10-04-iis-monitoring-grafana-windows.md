---
title: "IIS + Windows: szybki monitoring w Grafanie (Telegraf + InfluxDB)"
date: "2025-10-04"
slug: "iis-monitoring-grafana-windows"
draft: false
description: "Zbieramy metryki IIS (requests/sec, queue length, HTTP 500) i logi z access.log do InfluxDB 2.x z użyciem Telegrafa."
tags: ["IIS", "Monitoring", "Grafana", "InfluxDB", "Windows"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/iis-monitoring-grafana-windows.png"
canonical: "https://sqlmaniak.blog/iis-monitoring-grafana-windows"
---

Lead
----
IIS żyje – i to często pod SQL-owym backendem. Pokażę krótki pipeline metryk i logów do Grafany.

## Telegraf – performance countery
```toml
[[inputs.win_perf_counters]]
  [[inputs.win_perf_counters.object]]
    ObjectName = "Web Service"
    Counters = ["Current Connections","Get Requests/sec","Post Requests/sec"]
    Instances = ["_Total"]
```

## Telegraf – logi IIS (tail + grok)
```toml
[[inputs.tail]]
  files = ["C:/inetpub/logs/LogFiles/W3SVC1/u_ex*.log"]
  from_beginning = false
  data_format = "grok"
  grok_patterns = ['%{TIMESTAMP_ISO8601:time} %{IPORHOST:client} %{WORD:method} %{URIPATHPARAM:uri} %{NUMBER:status:int} %{NUMBER:sc_substatus:int} %{NUMBER:sc_win32_status:int} %{NUMBER:time_taken:int}']
```

## W Grafanie
- Panel `HTTP 5xx`, `Average time_taken`, `Requests/sec`.  
- Alert: `5xx rate > 1% przez 5m`.

## Pro tip
Zsynchronizuj zegary (NTP) — inaczej korelacja metryk/logów to horror.
