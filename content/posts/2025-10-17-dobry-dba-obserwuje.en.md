---
title: "A Good DBA Does Not Guess — They Observe"
date: 2025-10-17
slug: dobry-dba-obserwuje
tags: [SQLServer, Monitoring, Grafana, InfluxDB, Telegraf, DevOps, DataPlatform]
draft: false
---

Every chart tells a story. CPU, I/O, memory, and queries all reveal what is really happening on a server. A good DBA does not merely react to an alert — they understand *why* it appeared.

My favorite stack is **Telegraf + InfluxDB + Grafana**. Together they form a cockpit: **SQLManiak Monitoring**. Not a dashboard designed just to look pretty, but a **map of system awareness** where every metric has meaning.

> “Knowledge begins where guessing ends.”

---

### From reacting to observing

Most performance problems do not appear overnight. They develop quietly between successive `BACKUP` and `CHECKDB` operations and one too many long-running `SELECT *` queries. Without monitoring, we see only the outcome: a red alert, longer response times, or falling PLE.

Monitoring is not magic. It is **awareness over time** — an event history that shows how a server actually behaves. When something breaks, the goal is not to panic, but to *understand*.

---

### What makes up my cockpit

Each component has a distinct role:

- **Telegraf** collects data from SQL Server, Windows, IIS, and the network. Plugins such as `inputs.sqlserver`, `inputs.win_perf_counters`, `inputs.tail` (for IIS logs), and `inputs.ping` provide a broad system view.

- **InfluxDB** stores time-series metrics. Each point represents an observation at a moment in time: `cpu_usage`, `wait_stats`, `tempdb_free_space`, `connections_active`. Buckets and retention policies preserve both recent and historical information.

- **Grafana** visualizes that information — a mirror of system awareness. Dashboards show trends, while alerts identify deviations from expected behavior. The point is not colorful charts, but being able to decide what to do next at a glance.

---

### What the dashboard shows

My dashboard has several sections:

1. **System** — CPU, RAM, I/O, and network. The server's breathing rhythm and resource consumption.
2. **SQL Server** — PLE, PAGEIOLATCH, THREADPOOL, tempdb usage, and active sessions. Where SQL Server reveals what hurts.
3. **Storage and logs** — disk latency, write latency, IOPS, and transaction-log statistics. Where theory meets physics.
4. **Query Insights** — the top 10 queries by CPU time, logical reads, and writes. Here you can see what really consumes processing time.
5. **Alerts and anomalies** — thresholds and trends that flag unusual behavior. Reliability begins with noticing what *deviates from normal*.

---

### Why Performance Monitor alone is not enough

Charts in `perfmon.msc` tell you that something is happening, but not necessarily *why*. Grafana lets you compare context: CPU versus sessions, I/O versus queries, memory versus tempdb. **Correlating charts** reveals relationships that individual counters cannot show.

You do not guess or panic. You look — and you see.

---

### The philosophy of observation

Being a DBA is a little like being an astrophysicist: you cannot stop a star, but you can understand why it shines differently today than yesterday.

SQL Server is also a living organism in this metaphor. It has a rhythm, memory, quirks, and its own response time. Understanding comes when you stop focusing solely on errors and start examining their *causes*.

> “Monitoring is not a tool. It is a way of thinking.”

---

### Experiment

Install locally:

```bash
choco install telegraf influxdb grafana
```

Configure:

```toml
[[outputs.influxdb_v2]]
  urls = ["http://localhost:8086"]
  token = "$INFLUX_TOKEN"
  organization = "Demo"
  bucket = "Monitoring"
```

Add the plugin:

```toml
[[inputs.sqlserver]]
  servers = ["Server=localhost;User ID=telegraf;Password=Secret;app name=SQLMonitor"]
```

Start Grafana, add InfluxDB as a data source, and import a dashboard. The first view is always surprising: suddenly the server *starts talking*.

---

Understanding is the beginning of control. A good DBA does not guess — they observe. That is why their servers remain calm even when everything around them seems to be on fire.
