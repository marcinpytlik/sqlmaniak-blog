---
title: "Zabbix — monitoring infrastruktury i aplikacji — 4-dniowe szkolenie praktyczne"
date: "2026-10-02"
slug: "zabbix-monitoring-szkolenie-praktyczne"
draft: false
description: "Praktyczne 4-dniowe szkolenie z Zabbix: server, Agent2, proxy, items, triggers, templates, discovery, Windows, Linux, SQL Server, SNMP, HTTP checks, alerting, API i Monitoring Day."
tags: ["Zabbix", "Monitoring", "Linux", "Windows Server", "SQL Server", "Observability", "Szkolenia"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/zabbix-monitoring-szkolenie-praktyczne/"
---

Monitoring ma być systemem wczesnego ostrzegania i źródłem danych do diagnozy, a nie tylko ścianą zielonych i czerwonych ikon.

Właśnie temu służy moje szkolenie **„Zabbix — monitoring infrastruktury i aplikacji”** — cztery dni praktycznej pracy od instalacji i Agent2, przez items, triggers i templates, aż do monitoringu Windows, Linux, SQL Server, logów, HTTP, alertingu i końcowego Monitoring Day.

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone dla:
- administratorów systemów,
- administratorów SQL Server,
- zespołów infrastrukturalnych,
- inżynierów DevOps i operations,
- osób odpowiedzialnych za monitoring usług i aplikacji.

## Program — 4 dni

### Dzień 1 — architektura i instalacja Zabbix

- architektura Zabbix,
- Zabbix Server,
- frontend i database,
- Agent i Agent2,
- proxy,
- passive i active checks,
- hosts i host groups,
- interfaces,
- instalacja i podstawowa konfiguracja,
- komunikacja i porty.

### Dzień 2 — Items, Triggers, Templates i Discovery

- item types,
- keys,
- preprocessing,
- dependent items,
- trigger expressions,
- severities,
- dependencies,
- macros,
- templates,
- low-level discovery,
- discovery rules,
- tags i event correlation.

### Dzień 3 — monitoring produkcyjny

- Windows Server,
- Linux,
- services i processes,
- filesystem i capacity,
- log monitoring,
- SNMP,
- HTTP checks,
- custom UserParameters,
- SQL Server,
- podstawowe custom metrics,
- actions, media types i notifications.

### Dzień 4 — troubleshooting, API i Monitoring Day

- Zabbix proxy,
- queue,
- housekeeping,
- performance,
- permissions,
- dashboards,
- maps,
- Zabbix API,
- automatyzacja konfiguracji,
- troubleshooting agent/server,
- końcowy Monitoring Day.

## Monitoring Day

Uczestnik dostaje działające środowisko, w którym pojawiają się kontrolowane problemy:
- zatrzymana usługa,
- niedostępny host,
- pełny filesystem,
- problem z endpointem HTTP,
- błąd w logu,
- niedziałający SQL Server check,
- niepoprawny trigger lub template.

Proces pracy wygląda następująco:

**event → trigger → evidence → root cause → recovery**

## Rezultat szkolenia

Po szkoleniu uczestnik potrafi zbudować monitoring Zabbix dla infrastruktury i aplikacji, tworzyć własne items, triggers i templates, konfigurować alerting oraz diagnozować problemy na podstawie danych z systemu monitoringu.

## Forma organizacyjna

Szkolenie trwa **4 dni** i może być prowadzone stacjonarnie lub online.

Pełny opis usług znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać środowisko, źródła danych oraz zakres monitoringu.
