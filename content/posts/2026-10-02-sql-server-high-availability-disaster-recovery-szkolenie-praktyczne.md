---
title: "SQL Server High Availability i Disaster Recovery — 5-dniowe szkolenie praktyczne"
date: "2026-10-02"
slug: "sql-server-high-availability-disaster-recovery-szkolenie-praktyczne"
draft: false
description: "Praktyczne 5-dniowe szkolenie z High Availability i Disaster Recovery w SQL Server: WSFC, FCI, Log Shipping, Availability Groups, Distributed AG, monitoring, troubleshooting i Disaster Day."
tags: ["SQL Server", "High Availability", "Disaster Recovery", "Always On", "WSFC", "FCI", "Szkolenia"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/sql-server-high-availability-disaster-recovery-szkolenie-praktyczne/"
---

Wysoka dostępność nie zaczyna się od zaznaczenia opcji Enable Always On Availability Groups.

Zaczyna się znacznie wcześniej: od storage, sieci, quorum, kont usług, DNS, zależności klastra i odpowiedzi na dwa podstawowe pytania:

- ile danych możemy stracić,
- jak długo system może być niedostępny.

Właśnie z tego założenia powstało moje szkolenie **„SQL Server High Availability i Disaster Recovery”** — pięć dni praktycznej pracy od fundamentów infrastruktury, przez FCI i Availability Groups, aż do Distributed AG, monitoringu, kontrolowanych awarii i końcowego Disaster Day.

To nie jest szkolenie polegające na przechodzeniu przez kreatory. Celem jest zrozumienie, **co dzieje się pod spodem, jak rozpoznać awarię i jak bezpiecznie przywrócić środowisko do działania**.

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone przede wszystkim dla:

- administratorów SQL Server,
- administratorów systemów Windows pracujących z SQL Server,
- osób odpowiedzialnych za utrzymanie środowisk krytycznych,
- architektów projektujących rozwiązania HA/DR,
- zespołów, które utrzymują FCI lub Availability Groups i chcą lepiej rozumieć zależności infrastrukturalne,
- administratorów przygotowujących procedury awaryjne, patching i runbooki DR.

Uczestnik powinien znać podstawy administracji SQL Server oraz swobodnie poruszać się w SQL Server Management Studio lub Visual Studio Code.

Pomocna jest podstawowa znajomość Windows Server, Active Directory i sieci TCP/IP.

## Jak wygląda praca podczas szkolenia?

Każdy blok ma podobny rytm:

1. krótkie omówienie mechanizmu,
2. demonstracja prowadzącego,
3. wykonanie zadania przez uczestnika,
4. kontrolowany problem albo awaria,
5. zebranie danych,
6. postawienie hipotezy,
7. potwierdzenie przyczyny,
8. naprawa i ponowna walidacja.

Nie chodzi więc tylko o to, żeby konfiguracja była zielona.

Uczestnik ma nauczyć się przejścia:

**dane → hipoteza → weryfikacja → przyczyna → naprawa → potwierdzenie działania**

## Jedno środowisko przez całe pięć dni

Szkolenie pracuje na przygotowanym środowisku domenowym z kilkoma serwerami SQL Server i dwoma klastrami WSFC.

W laboratoriach pojawiają się między innymi:

- Active Directory i konta usług,
- Windows Server Failover Clustering,
- iSCSI i shared storage,
- SQL Server Failover Cluster Instance,
- SQL Server Availability Groups,
- listenery i HADR endpoints,
- Distributed Availability Groups,
- Zabbix,
- Transactional Replication.

Środowisko jest budowane warstwowo. Kolejne laboratoria wykorzystują elementy przygotowane wcześniej, dzięki czemu uczestnik widzi zależności między storage, klastrem, SQL Server i warstwą kliencką.

## Program — 5 dni / 40 godzin dydaktycznych

### Dzień 1 — fundamenty HA, storage i WSFC

Pierwszy dzień zaczynamy od architektury i infrastruktury:

- High Availability vs Disaster Recovery,
- RPO, RTO i SLA,
- NTFS vs ReFS,
- sektory i allocation unit,
- latency storage,
- shared storage i iSCSI,
- MPIO,
- Windows Server Failover Cluster,
- quorum, witness i voting,
- budowa i walidacja klastra,
- DNS, VNN, heartbeat i multi-subnet,
- podstawowa diagnostyka WSFC.

### Dzień 2 — FCI i klasyczne mechanizmy DR

Drugiego dnia przechodzimy do mechanizmów SQL Server:

- architektura SQL Server Failover Cluster Instance,
- instalacja i zasoby klastra SQL,
- failover FCI,
- zachowanie klientów podczas przełączenia,
- cluster log i SQL Server error log,
- zależności storage i sieci,
- Log Shipping,
- RPO/RTO w Log Shipping,
- konfiguracja i test awarii,
- Database Mirroring jako mechanizm historyczny i model edukacyjny,
- safety modes, witness i failover,
- porównanie FCI, Log Shipping i Mirroring.

### Dzień 3 — Always On Availability Groups

Trzeci dzień jest poświęcony Availability Groups:

- architektura AG,
- synchronous i asynchronous commit,
- automatic i manual failover,
- HADR endpoints,
- logins, permissions i prerequisites,
- tworzenie Availability Group,
- listener, DNS i VNN,
- zachowanie klientów,
- MultiSubnetFailover,
- manualny i automatyczny failover,
- DMV,
- synchronization state i health,
- log send queue,
- redo queue,
- diagnostyka problemów AG.

### Dzień 4 — Advanced AG i Distributed Availability Groups

Czwarty dzień rozwija AG o scenariusze produkcyjne:

- readable secondary,
- ApplicationIntent=ReadOnly,
- read-only routing,
- routing URL i routing list,
- walidacja routingu po failoverze,
- backup preference,
- backup priority,
- role-aware SQL Agent jobs,
- Distributed Availability Groups,
- global primary i forwarder,
- automatic seeding,
- monitoring DAG,
- planned DR failover,
- walidacja last_hardened_lsn,
- scenariusze awarii między lokalizacjami.

## Dzień 5 — monitoring, troubleshooting, replikacja i Disaster Day

Ostatni dzień skupia się na operacyjnej stronie HA/DR:

- co monitorować w WSFC, FCI i AG,
- DMV, Extended Events, Performance Counters i logi,
- pomiar technicznego opóźnienia transportu,
- monitoring HA w Zabbix,
- alerting dla replica health, kolejek i zasobów klastra,
- Transactional Replication: Publisher, Distributor i Subscriber,
- monitoring backlogu i agentów replikacji,
- projekt architektury dla systemu krytycznego,
- kontrolowane awarie,
- recovery,
- podsumowanie RPO/RTO.

Finałem jest **Disaster Day**.

## Disaster Day — środowisko przestaje być idealne

W ostatniej części szkolenia uczestnik dostaje działające środowisko, a następnie pojawiają się kontrolowane problemy, na przykład:

- zatrzymany HADR endpoint,
- niedziałający listener,
- problem DNS,
- replika NOT SYNCHRONIZING,
- replika w stanie RESOLVING,
- rosnący log send queue,
- rosnący redo queue,
- błędny read-only routing,
- niedostępny node,
- problem z zasobem klastra,
- problem z quorum lub witness.

Nie dostaje od razu informacji, gdzie znajduje się przyczyna.

Musi zebrać dane, zbudować hipotezę, potwierdzić ją i dopiero wtedy wykonać recovery.

## Monitoring nie kończy się na zielonym statusie

Jednym z ważniejszych elementów szkolenia jest nauka interpretacji stanu środowiska.

Dla Availability Groups analizujemy między innymi:

- connected state,
- synchronization state,
- synchronization health,
- log send queue,
- redo queue,
- send/redo rate,
- last hardened LSN,
- last commit time.

Dla WSFC patrzymy na:

- stan nodów,
- owner node,
- zasoby klastra,
- quorum i witness,
- sieć.

Dla FCI:

- owner zasobów SQL,
- Network Name i IP,
- zależności,
- storage.

Monitoring ma powiedzieć **gdzie zacząć diagnostykę**, a nie zastąpić samą diagnostykę.

## Replikacja — dystrybucja danych, nie kolejny mechanizm failover

W szkoleniu pojawia się również Transactional Replication.

Celowo pokazuję ją obok HA/DR, żeby dobrze oddzielić dwa różne problemy.

W laboratorium pracujemy z:

- Publisher,
- Distributor,
- Subscriber,
- Snapshot Agent,
- Log Reader Agent,
- Distribution Agent,
- publication i subscription,
- backlogiem,
- zatrzymaniem Distribution Agent,
- catch-up po wznowieniu.

Uczestnik widzi również, dlaczego Subscriber **nie staje się automatycznie serwerem DR**.

## Materiały szkoleniowe

Środowisko zawiera zestaw laboratoriów, skryptów i materiałów operacyjnych, między innymi:

- checklisty przed rozpoczęciem dnia,
- mapę środowiska,
- runbook prowadzącego,
- scenariusze failure injection,
- oczekiwane wyniki laboratoriów,
- procedury resetu i recovery,
- materiały troubleshootingowe,
- końcowy case study.

Materiały są przygotowane tak, żeby można było wracać do konkretnych scenariuszy również po szkoleniu.

## Czego to szkolenie nie robi?

Szkolenie koncentruje się na **SQL Server High Availability i Disaster Recovery w środowisku on-premises**.

Nie jest to kurs Azure ani szkolenie z platform chmurowych.

Nie zastępuje również pełnego szkolenia z:

- administracji Active Directory,
- zaawansowanej administracji storage,
- performance tuningu całej instancji,
- bezpieczeństwa SQL Server.

Te obszary pojawiają się tylko tam, gdzie mają bezpośredni wpływ na HA/DR.

## Forma organizacyjna

Szkolenie trwa **5 dni / 40 godzin dydaktycznych**, w układzie **09:00–15:00**.

Najlepiej sprawdza się jako zamknięte szkolenie dla zespołu, który administruje lub projektuje środowiska SQL Server wymagające wysokiej dostępności.

Może być prowadzone stacjonarnie lub online, po wcześniejszym uzgodnieniu środowiska uczestników.

Pełny opis usług znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać środowisko, poziom zespołu oraz oczekiwany rezultat szkolenia.
