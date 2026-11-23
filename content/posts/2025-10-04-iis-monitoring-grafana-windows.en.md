---
title: "IIS and Windows: quick monitoring with Grafana, Telegraf and InfluxDB"
date: "2025-10-04"
slug: "iis-monitoring-grafana-windows-en"
draft: false
description: "Collect IIS metrics and access logs with Telegraf and visualize them in Grafana using InfluxDB 2.x."
tags: ["IIS","Monitoring","Grafana"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/iis-monitoring-grafana-windows.png"

---

## Introduction
IIS often sits in front of a SQL Server backend. Here is a compact metrics-and-logs pipeline for Grafana.

## Telegraf: performance counters
```toml
[[inputs.win_perf_counters]]
  [[inputs.win_perf_counters.object]]
    ObjectName = "Web Service"
    Counters = ["Current Connections","Get Requests/sec","Post Requests/sec"]
    Instances = ["_Total"]
```

## Telegraf: IIS logs (tail and grok)
```toml
[[inputs.tail]]
  files = ["C:/inetpub/logs/LogFiles/W3SVC1/u_ex*.log"]
  from_beginning = false
  data_format = "grok"
  grok_patterns = ['%{TIMESTAMP_ISO8601:time} %{IPORHOST:client} %{WORD:method} %{URIPATHPARAM:uri} %{NUMBER:status:int} %{NUMBER:sc_substatus:int} %{NUMBER:sc_win32_status:int} %{NUMBER:time_taken:int}']
```

## Grafana
- Panels: `HTTP 5xx`, `Average time_taken`, `Requests/sec`.
- Alert when the 5xx rate exceeds 1% for five minutes.

## Pro tip
Synchronize clocks with NTP; otherwise correlating logs and metrics becomes painful.
