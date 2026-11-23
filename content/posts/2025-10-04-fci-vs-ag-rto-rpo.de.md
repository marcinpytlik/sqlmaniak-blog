---
title: "FCI oder Always On AG: Architekturwahl und RTO/RPO"
date: "2025-10-04"
slug: "fci-vs-ag-rto-rpo-de"
draft: false
description: "Ein praxisnaher Vergleich von FCI und AG mit Entscheidungsszenarien und messbaren Wiederherstellungszielen."
tags: ["SQL Server","FCI","AlwaysOn AG"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/fci-vs-ag-rto-rpo.png"

---

## Einleitung
FCI und AG sind nicht grundsätzlich „besser“ oder „schlechter“. Beide passen zu unterschiedlichen Anforderungen. Entscheiden wir systematisch.

## Kurz erklärt
- **FCI:** Hochverfügbarkeit auf *Instanzebene* mit gemeinsamem Storage; keine Skalierung von Lesezugriffen.
- **AG:** Verfügbarkeit auf *Datenbankebene* mit lesbaren Replikaten und unabhängigem Storage.

## Wann FCI sinnvoll ist
- Ein SAN ist vorhanden und Änderungen an Anwendungen sollen minimal bleiben.
- Migration älterer Instanzen mit Abhängigkeiten von `msdb` oder `master`.
- Beispielziele: RTO etwa 1–2 Minuten und RPO nahe null bei gemeinsamem Storage; durch Tests bestätigen.

## Wann AG sinnvoll ist
- Lesezugriffe sollen auf sekundäre Replikate verteilt werden.
- Jeder Knoten verfügt über unabhängigen Storage.
- Disaster Recovery an einem zweiten Standort mit synchronem oder asynchronem Modus.

## Messen statt vermuten
- Miss Neustartdauer der Instanz, Recovery der größten Datenbank und Netzwerkverhalten zwischen Knoten.
- RTO = Fehlererkennung + Failover + Recovery.
- Bei asynchroner AG hängt RPO von den auf dem Sekundärsystem noch nicht dauerhaft gespeicherten Daten ab, nicht einfach vom Redo-Verzug.

## Entscheidungscheckliste
- [ ] Anwendungsanforderungen (Connection Strings, Listener?)
- [ ] Budget und Storage (SAN oder lokales NVMe)
- [ ] Read-only-Workloads?
- [ ] Enterprise-Lizenzierung erforderlich?
- [ ] Betriebsteam: Wer beherrscht die AG-Komplexität?

> Teste Failover vierteljährlich. Ungetestete HA bleibt ein Versprechen.
