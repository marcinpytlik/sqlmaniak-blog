---
title: "Grafana — monitoring i observability — 4-dniowe szkolenie praktyczne"
date: "2026-10-02"
slug: "grafana-observability-monitoring-szkolenie-praktyczne"
draft: false
description: "Praktyczne 4-dniowe szkolenie z Grafana: data sources, dashboards, variables, transformations, Prometheus, InfluxDB, Telegraf, Loki, LogQL, alerting, provisioning i Observability Day."
tags: ["Grafana", "Observability", "Monitoring", "Loki", "InfluxDB", "Prometheus", "Telegraf", "Szkolenia"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/grafana-observability-monitoring-szkolenie-praktyczne/"
---

Dobry dashboard nie jest celem samym w sobie.

Grafana ma pomóc odpowiedzieć na pytanie **co dzieje się z systemem, kiedy to się zaczęło i gdzie szukać przyczyny**. Dlatego szkolenie nie kończy się na tworzeniu paneli — łączy metryki, logi, alerting i korelację danych.

Właśnie temu służy moje szkolenie **„Grafana — monitoring i observability”** — cztery dni praktycznej pracy z dashboardami, data sources, Prometheus lub InfluxDB, Telegraf, Loki, LogQL, alertingiem i końcowym Observability Day.

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone dla:
- administratorów systemów,
- administratorów baz danych,
- DevOps i SRE,
- zespołów operations,
- osób budujących monitoring infrastruktury i aplikacji.

## Program — 4 dni

### Dzień 1 — Grafana i metryki

- architektura Grafana,
- data sources,
- dashboards,
- panels,
- queries,
- variables,
- transformations,
- thresholds,
- annotations,
- Prometheus i InfluxDB jako źródła danych,
- podstawy Telegraf.

### Dzień 2 — infrastruktura i SQL Server

- zbieranie metryk Windows i Linux,
- Telegraf,
- CPU, memory, disk i network,
- SQL Server metrics,
- własne zapytania,
- reusable dashboards,
- variables per host/instance,
- capacity i trend analysis,
- projektowanie dashboardów operacyjnych.

### Dzień 3 — logi i observability

- Loki,
- labels,
- log streams,
- LogQL,
- filtrowanie i agregacja logów,
- correlation metrics ↔ logs,
- annotations,
- troubleshooting z wielu źródeł,
- podstawy trace correlation.

### Dzień 4 — alerting, provisioning i Observability Day

- alert rules,
- contact points,
- notification policies,
- silences i mute timings,
- provisioning,
- dashboard as code,
- folders i permissions,
- utrzymanie środowiska,
- backup konfiguracji,
- końcowy Observability Day.

## Observability Day

W końcowym scenariuszu uczestnik dostaje kilka objawów jednocześnie:
- CPU spike,
- rosnące SQL waits,
- blocking,
- pogorszenie czasu odpowiedzi aplikacji,
- błędy widoczne w Loki.

Zadaniem jest skorelować metryki i logi, ustalić kolejność zdarzeń oraz wskazać najbardziej prawdopodobne źródło problemu.

## Przykładowy stack szkoleniowy

Środowisko może wykorzystywać:

- Grafana,
- InfluxDB lub Prometheus,
- Loki,
- Telegraf,
- Windows Server,
- Linux,
- SQL Server.

## Rezultat szkolenia

Po szkoleniu uczestnik potrafi podłączyć źródła danych do Grafana, budować użyteczne dashboardy, pracować z metrykami i logami, tworzyć alerty i wykorzystywać observability do rzeczywistego troubleshooting.

## Forma organizacyjna

Szkolenie trwa **4 dni** i może być prowadzone stacjonarnie lub online.

Pełny opis usług znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać źródła danych, obecną architekturę monitoringu oraz oczekiwany rezultat szkolenia.
