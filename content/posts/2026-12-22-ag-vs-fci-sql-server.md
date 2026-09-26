---
title: "AG czy FCI — co właściwie rozwiązują i czego nie rozwiązują"
date: 2026-12-22T20:00:00+01:00
slug: ag-vs-fci-sql-server
description: "Porównanie Availability Groups i Failover Cluster Instance w SQL Server: zakres ochrony, storage, failover i typowe nieporozumienia."
tags: [SQLServer, AlwaysOn, AvailabilityGroups, FCI, HighAvailability]
categories: [SQL Server]
draft: false
---

Availability Groups i Failover Cluster Instance często trafiają do jednego worka pod nazwą „HA”.

Oba rozwiązania zwiększają dostępność, ale chronią system w inny sposób.

## FCI

Failover Cluster Instance chroni instancję SQL Server. W typowej architekturze wiele węzłów klastra korzysta ze współdzielonego storage.

Po failover usługa SQL Server uruchamia się na innym węźle, a aplikacja nadal korzysta z nazwy wirtualnej instancji.

## Availability Groups

Availability Group pracuje na poziomie baz danych. Każda replika ma własną kopię danych.

Listener daje aplikacji stabilny punkt połączenia.

## Najważniejsza różnica

FCI:

- chroni instancję,
- nie tworzy drugiej kopii danych na poziomie storage SQL,
- obejmuje obiekty instancji.

AG:

- chroni wybrane bazy,
- utrzymuje osobne kopie danych,
- wymaga osobnego podejścia do loginów, jobów i innych obiektów instancji.

## Failover to nie backup

Ani AG, ani FCI nie zastępują backupu. HA i DR rozwiązują inne problemy niż możliwość odtworzenia danych do punktu w czasie.

## Co sprawdzić przed wyborem?

- co dokładnie ma być chronione,
- jakie są RTO i RPO,
- czy potrzebujesz drugiej kopii danych,
- czy masz współdzielony storage,
- jak będą obsługiwane loginy i joby,
- czy potrzebujesz read-only replica.

## Podsumowanie

Pytanie „AG czy FCI?” jest za krótkie.

Najpierw trzeba ustalić, przed jaką awarią chronimy system i jaki zakres ma mieć failover.