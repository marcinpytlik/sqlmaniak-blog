---
title: "Administracja IIS na Windows Server 2022 Core — 4-dniowe szkolenie praktyczne"
date: "2026-10-02"
slug: "administracja-iis-windows-server-2022-core-szkolenie-praktyczne"
draft: false
description: "Praktyczne 4-dniowe szkolenie z administracji IIS na Windows Server 2022 Core: zdalne zarządzanie, bezpieczeństwo, HTTPS, ASP.NET Core, monitoring, troubleshooting, backup/restore i hardening."
tags: ["IIS", "Windows Server 2022", "PowerShell", "ASP.NET Core", "Szkolenia"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/administracja-iis-windows-server-2022-core-szkolenie-praktyczne/"
---

Administracja IIS nie musi oznaczać logowania się pulpitem do każdego serwera i przeklikiwania konfiguracji lokalnie.

W tym szkoleniu pracujemy inaczej.

Serwery WEB01 i WEB02 działają na **Windows Server 2022 Core**, a administracja odbywa się z dedykowanej stacji zarządzającej przy użyciu **IIS Manager, Server Manager, RSAT i PowerShell**.

To czterodniowe szkolenie praktyczne, którego celem jest zbudowanie pełnego obrazu pracy z IIS: od instalacji i architektury, przez bezpieczeństwo i hosting aplikacji, aż po monitoring, troubleshooting, automatyzację, backup/restore i hardening.

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone przede wszystkim dla:

- administratorów Windows Server,
- administratorów aplikacyjnych,
- zespołów utrzymujących środowiska IIS,
- osób odpowiedzialnych za publikację aplikacji .NET / ASP.NET Core,
- administratorów, którzy chcą uporządkować zdalne zarządzanie i automatyzację IIS,
- zespołów przygotowujących runbooki, procedury recovery i standardy hardeningu.

Pomocna jest podstawowa znajomość Windows Server, Active Directory, DNS i PowerShell.

## Jak pracujemy?

Szkolenie ma charakter warsztatowy.

Każdy blok łączy:

1. krótkie omówienie mechanizmu,
2. demonstrację,
3. wykonanie zadania przez uczestnika,
4. walidację konfiguracji,
5. kontrolowany scenariusz awarii albo challenge.

Ważna zasada przewija się przez wszystkie cztery dni:

**najpierw dowody, potem zmiana konfiguracji.**

## Środowisko szkoleniowe

Pracujemy w domenie `sqllab.local` na środowisku:

- HOST — stacja administracyjna z GUI, IIS Manager, Server Manager, RSAT i PowerShell,
- DC01 — Windows Server 2022 Core, Active Directory i DNS,
- WEB01 — Windows Server 2022 Core + IIS,
- WEB02 — Windows Server 2022 Core + IIS.

Serwery IIS nie wymagają Desktop Experience.

## Program — 4 dni

### Dzień 1 — IIS Fundamentals

Pierwszy dzień buduje podstawowy model działania IIS:

- Windows Server 2022 Core i zdalna administracja,
- instalacja IIS,
- WMSVC i zdalny IIS Manager,
- Sites, Applications i Virtual Directories,
- bindings i host headers,
- Application Pools,
- `w3wp.exe`,
- podstawy `applicationHost.config`.

### Dzień 2 — Security & Application Hosting

Drugiego dnia przechodzimy do bezpieczeństwa i hostowania aplikacji:

- Anonymous Authentication i Windows Authentication,
- Application Pool Identity,
- uprawnienia NTFS i least privilege,
- HTTPS, certyfikaty i SNI,
- hosting ASP.NET Core za IIS,
- .NET Hosting Bundle i ASP.NET Core Module.

### Dzień 3 — Monitoring & Troubleshooting

Trzeci dzień skupia się na diagnostyce:

- IIS W3C logs,
- HTTPERR,
- `sc-status`, `sc-substatus`, `sc-win32-status`,
- Failed Request Tracing (FREB),
- worker processes,
- performance counters,
- problemy 401, 403, 404, 500 i 503,
- kontrolowane scenariusze broken IIS.

Pracujemy według schematu:

**DNS → TCP → HTTP → logi → FREB → binding → Application Pool → worker process → authentication → NTFS**

### Dzień 4 — Automation, Recovery & Production

Ostatni dzień domyka szkolenie operacyjnie:

- PowerShell i automatyzacja,
- walidatory środowiska,
- backup konfiguracji IIS,
- restore,
- configuration history,
- Request Filtering,
- hardening,
- checklisty operacyjne,
- final challenge.

## Final Challenge

Na zakończenie uczestnik buduje od podstaw usługę `ServicePortal`.

Musi samodzielnie:

- utworzyć witrynę i dedykowany Application Pool,
- nadać minimalne wymagane uprawnienia NTFS,
- skonfigurować Windows Authentication,
- przygotować HTTPS i SNI,
- przypisać certyfikat,
- zastosować Request Filtering,
- przygotować backup konfiguracji,
- przeprowadzić kontrolowaną awarię,
- odtworzyć konfigurację,
- ponownie potwierdzić poprawność działania.

## Materiały szkoleniowe

Repozytorium szkoleniowe zawiera:

- 16 laboratoriów,
- challenge na zakończenie każdego dnia,
- rozwiązania referencyjne,
- skrypty PowerShell,
- failure injection,
- walidatory Day 1–4,
- demo ASP.NET Core,
- trainer runbook,
- participant quick start,
- preflight checklist.

## Rezultat

Po szkoleniu uczestnik potrafi samodzielnie zbudować, zabezpieczyć, monitorować, diagnozować i odtworzyć środowisko IIS działające na Windows Server 2022 Core — bez potrzeby lokalnej pracy na graficznym pulpicie serwera.

## Forma organizacyjna

Szkolenie trwa **4 dni**, w układzie **09:00–16:00**.

Najlepiej sprawdza się jako zamknięte szkolenie dla zespołu administratorów lub zespołu utrzymującego aplikacje działające na IIS.

Może być prowadzone stacjonarnie lub online, po wcześniejszym uzgodnieniu środowiska i poziomu uczestników.

Pełny opis usług znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać środowisko, poziom zespołu oraz oczekiwany rezultat szkolenia.