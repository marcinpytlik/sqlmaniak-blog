---
title: "Dobry DBA nie zgaduje – obserwuje"
date: 2025-10-17
slug: dobry-dba-obserwuje
tags: [SQLServer, Monitoring, Grafana, InfluxDB, DevOps, DataPlatform]
draft: false
---

Każdy wykres to historia. CPU, I/O, pamięć, zapytania – wszystkie mówią, co naprawdę dzieje się na serwerze.  
Dobry DBA nie reaguje na alarm, tylko rozumie, *dlaczego* on się pojawił.  

Mój ulubiony zestaw: Telegraf + InfluxDB + Grafana.  
Z tego powstaje mój cockpit: SQLManiak Monitoring.

> „Wiedza zaczyna się tam, gdzie kończą się zgadywania.”

Pokażę Ci, jak wygląda dashboard, na którym widać bicie serca SQL Servera.
