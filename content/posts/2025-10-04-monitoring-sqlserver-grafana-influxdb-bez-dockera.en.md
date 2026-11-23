---
title: "Monitoring SQL Server 2022 with Grafana, InfluxDB and Telegraf (without Docker)"
date: "2025-10-04"
slug: "monitoring-sqlserver-grafana-influxdb-bez-dockera-en"
draft: false
description: "Step-by-step Windows setup for InfluxDB 2.x, Telegraf and Grafana, including SQL Server dashboards and alerts."
tags: ["Monitoring","Grafana","SQL Server"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/monitoring-sqlserver-grafana-influxdb-bez-dockera.png"

---

## Introduction
Running Windows Server without Docker? You can still install InfluxDB 2.x, Telegraf and Grafana, then build dashboards for SQL Server 2022.

## InfluxDB 2.x on Windows
1. Install it as a service and configure an organization and bucket (for example `Demo` for both).
2. Generate an **API token** with bucket-level read/write permissions.

## Telegraf inputs for SQL Server and Windows
Relevant sections of `telegraf.conf`:
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
- Add InfluxDB as a Flux data source.
- Import dashboards: *SQL Server Overview*, *Waits*, *Tempdb* and *IO latency*.
- Configure alerts for no backup in 24 hours, `% Log Used > 80%` and `Tempdb Used > 70%`.

## Permissions and security
- Give the SQL login `telegraf` the `VIEW SERVER PERFORMANCE STATE` permission and access to the required views/DMVs.
- Store passwords in Windows Credential Manager or a separate environment file.

## Verification
- Confirm that measurements arrive in the bucket and panels render without errors.
- Trigger a controlled test of the log-utilization alert and verify notification delivery.

> Repository bonus: add `monitoring/telegraf.conf`, `grafana/dashboard.json` and a `README.md` with installation and troubleshooting steps.
