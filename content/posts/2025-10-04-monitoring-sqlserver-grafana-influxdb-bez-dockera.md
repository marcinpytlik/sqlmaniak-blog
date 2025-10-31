---
title: "Monitoring SQL Server 2022 w Grafana + InfluxDB + Telegraf (bez Dockera)"
date: "2025-10-04"
slug: "monitoring-sqlserver-grafana-influxdb-bez-dockera"
draft: false
description: "Instalacja krok po kroku na Windows: InfluxDB 2.x, Telegraf i Grafana, plus gotowe dashboardy i alerty pod SQL Server 2022."
tags: ["Monitoring", "Grafana", "InfluxDB", "Telegraf", "SQL Server", "Windows"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/monitoring-sqlserver-grafana-influxdb-bez-dockera.png"
canonical: "https://sqlmaniak.blog/monitoring-sqlserver-grafana-influxdb-bez-dockera"
---

Lead
----
Masz Windows Server i nie chcesz Dockera? Da się. Poniżej komplet: instalacja InfluxDB 2.x, Telegraf, Grafana oraz przykładowe dashboardy dla SQL Server 2022.

## InfluxDB 2.x (Windows)
1. Zainstaluj jako usługę. Skonfiguruj org i bucket (np. org: `Demo`, bucket: `Demo`).  
2. Wygeneruj **API Token** o zasięgu `read/write` dla bucketa.

## Telegraf – inputy dla SQL i Windows
Plik `telegraf.conf` (fragmenty):
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
- Dodaj źródło danych InfluxDB (Flux).  
- Importuj dashboardy: *SQL Server Overview*, *Waits*, *Tempdb*, *IO latency*.
- Alerty: brak backupu 24h, `% Log Used > 80%`, `Tempdb Used > 70%`.

## Uprawnienia i bezpieczeństwo
- Konto `telegraf` w SQL: rola `VIEW SERVER PERFORMANCE STATE` + dedykowane widoki/DMV.  
- Hasła w Windows Credential Manager lub w osobnym pliku środowiskowym.

## Weryfikacja
- Panel zdrowia: punkty pomiarowe w buckecie rosną, wykresy bez błędów.  
- Test alertu: sztucznie podnieś `% Log Used` i sprawdź powiadomienie.

> Bonus: repo‑ready
Dodaj `\monitoring	elegraf.conf`, `\grafana\dashboard.json`, `README.md` z krokami i sekcją „Troubleshooting”.
