---
title: "FCI vs Always On AG: co wybrać i jak myśleć o RTO/RPO"
date: "2025-10-04"
slug: "fci-vs-ag-rto-rpo"
draft: false
description: "Porównanie w praktyce: kiedy FCI, kiedy AG, i jak policzyć RTO/RPO bez zgadywania. Proste scenariusze decyzyjne."
tags: ["SQL Server", "FCI", "AlwaysOn AG", "HA/DR", "Architecture"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/fci-vs-ag-rto-rpo.png"
canonical: "https://sqlmaniak.blog/fci-vs-ag-rto-rpo"
---

Lead
----
FCI i AG to nie „lepsze/gorsze”, tylko „odpowiednie do kontekstu”. Zróbmy to decyzyjnie.

## Jedno zdanie
- **FCI**: wysoka dostępność na poziomie *instancji* (współdzielone storage), brak skalowania odczytów.  
- **AG**: dostępność na poziomie *bazy*, repliki do odczytu, niezależne storage.

## Kiedy FCI
- Masz SAN i chcesz minimalnej zmiany w aplikacji.  
- Migracja starych instancji, zależności na `msdb`/`master`.  
- Proste RTO ~1–2 min, RPO ~0 (ta sama macierz).

## Kiedy AG
- Potrzebujesz odczytów z replik.  
- Niezależne storage na każdym węźle.  
- DR do innej lokalizacji; tryb synch/async.

## Liczby, nie przeczucia
- Zmierz: czas restartu instancji, recovery największej bazy, sieć między węzłami.  
- RTO = detekcja awarii + failover + recovery.  
- RPO przy AG async ≈ opóźnienie redo w DR.

## Checklista decyzji
- [ ] Wymagania aplikacji (connection stringi, listener?)  
- [ ] Budżet i storage (SAN vs lokalne NVMe)  
- [ ] Czytelnicy read‑only?  
- [ ] Licencje Enterprise?  
- [ ] Zespół operacyjny: kto obsłuży złożoność AG?

> Pamiętaj o testach failover co kwartał. HA bez ćwiczeń to ładna opowieść.
