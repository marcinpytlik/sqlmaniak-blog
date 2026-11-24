---
title: "SQL Server 2025 — Eine neue Ära der Datenverarbeitung"
date: 2025-11-19
tags: [SQL Server, SQL Server 2025, Performance, Monitoring, Security, Query Store, JSON]
categories: [SQLManiak]
draft: false
---

SQL Server 2025 (17.x) bringt wichtige Änderungen für DBAs, Architekten und Entwickler — insbesondere bei der Abfrageverarbeitung, neuen Datentypen, KI-Integration und Workload-Verwaltung. Dabei müssen allgemein verfügbare Funktionen von solchen unterschieden werden, die **PREVIEW_FEATURES** benötigen.

Dieser Überblick basiert auf der offiziellen Microsoft-Dokumentation und nicht auf unbestätigten Funktionsnamen.

## Intelligent Query Processing und Query Store

SQL Server 2025 erweitert die Familie **Intelligent Query Processing (IQP)**:

- **Optional Parameter Plan Optimization (OPPO)** — nutzt die Multiplan-Infrastruktur für Planvarianten bei Abfragen mit optionalen Prädikaten.
- **Cardinality Estimation Feedback for Expressions** — lernt geeignete Kardinalitätsschätzmodelle für Ausdrücke.
- **Degree of Parallelism (DOP) Feedback** — standardmäßig aktiviert.
- **Query Store für lesbare sekundäre Replikate** — in unterstützten Konfigurationen standardmäßig aktiviert.
- **ABORT_QUERY_EXECUTION** — ein Hint, der weitere Ausführungen bekannter problematischer Abfragen verhindern kann.

Ein eigenständiges Produkt namens „Query Store 3.0“ ist nicht dokumentiert. Für die Performanceanalyse benötigen wir weiterhin Ausführungspläne, Wait Statistics, Query Store und Anwendungsmessungen.

## Nativer JSON-Datentyp

SQL Server 2025 bietet den nativen Datentyp **`json`**, der JSON-Daten in einer optimierten binären Darstellung speichert.

Er heißt nicht **`JSONB`** — dieser Name ist vor allem aus PostgreSQL bekannt und bezeichnet nicht den SQL-Server-Datentyp.

Weitere JSON-Funktionen sind **`JSON_OBJECTAGG`** und **`JSON_ARRAYAGG`**. Vor einer Migration müssen Einschränkungen, Treiberkompatibilität, Indexverhalten und tatsächliche Abfrageperformance geprüft werden.

## VECTOR-Datentyp und KI

Der neue Datentyp **`vector`** speichert Vektorrepräsentationen für Ähnlichkeitssuche und verwandte Workloads.

Dazu gehören Funktionen wie **`VECTOR_DISTANCE`**, **`VECTOR_NORM`** und **`VECTOR_NORMALIZE`** sowie die Integration externer KI-Modelle.

**Wichtig:** Approximative Vektorindizes und bestimmte Vektorsuchfunktionen sind Preview-Features und benötigen eine passende **`PREVIEW_FEATURES`**-Konfiguration. Preview-Funktionen sind nicht automatisch für Produktion geeignet.

## Reguläre Ausdrücke und T-SQL

T-SQL unterstützt jetzt reguläre Ausdrücke, darunter:

- **`REGEXP_LIKE`** — Musterübereinstimmung prüfen;
- **`REGEXP_REPLACE`** — passende Textteile ersetzen;
- **`REGEXP_SUBSTR`** — passende Teilzeichenfolgen extrahieren;
- **`REGEXP_COUNT`** — Übereinstimmungen zählen.

Damit lassen sich manche Validierungs- und Transformationsaufgaben vereinfachen. Die Performance muss jedoch mit realen Workloads gemessen werden.

## Optimized Locking und TempDB

**Optimized Locking** reduziert den Speicherbedarf von Sperren und kann Blocking sowie Lock Escalation verringern. Prüfe Edition, Voraussetzungen und Datenbankkonfiguration.

SQL Server 2025 bietet außerdem **TempDB Space Resource Governance**, um die Folgen übermäßiger TempDB-Nutzung zu begrenzen, sowie **Accelerated Database Recovery in TempDB**.

Diese Verbesserungen beseitigen nicht jeden `PAGELATCH`-Wait und garantieren keine feste prozentuale Leistungssteigerung.

## Columnstore, Analytik und Integrationen

Zu den dokumentierten Columnstore-Neuerungen gehören **geordnete nichtclustered Columnstore-Indizes** und Verbesserungen beim Indexaufbau.

SQL Server 2025 erweitert zudem die Integration mit Microsoft Fabric und Datenwerkzeugen. Die Verfügbarkeit hängt von Edition, Konfiguration und Release-Status ab.

## Sicherheit und Deployment

Prüfe bei einer Migration die dokumentierten Änderungen bei Sicherheit, Verbindungen, Berechtigungen und Anwendungskompatibilität für den Ziel-Build.

Gehe nicht davon aus, dass offizielle Module namens „Security Shield“ oder „Secure Credential Vault“ existieren, wenn sie nicht in der Produktdokumentation aufgeführt sind.

Ebenso sollte man native offizielle ARM64-Containerimages für SQL Server oder clusterlose Availability Groups nicht allein aufgrund allgemeiner Plattformankündigungen voraussetzen.

## DBA-Checkliste vor dem Deployment

1. **Kompatibilität von Anwendungen und Treibern**, einschließlich neuer Datentypen.
2. **Query Store und Planregressionen** — Vergleich der Baseline vor und nach dem Upgrade.
3. **Preview-Funktionen** — Aktivierung und Eignung für die Umgebung.
4. **Verfügbarkeit je Edition** — Enterprise, Standard und Express.
5. **Backup-/Restore-, HA-/DR- und Performancetests** — eine neue Engine-Version ersetzt keine Betriebsvalidierung.

## Zusammenfassung

SQL Server 2025 bringt echte Neuerungen: natives `json`, `vector`, Regex-Funktionen, IQP-Verbesserungen, Optimized Locking und TempDB-Ressourcenschutz.

Der wichtigste DBA-Grundsatz bleibt unverändert: **Zuerst die Funktion in der offiziellen Dokumentation bestätigen und anschließend mit der eigenen Workload testen**.

Quellen:

- [What's New in SQL Server 2025 — Microsoft Learn](https://learn.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-2025?view=sql-server-ver17)
- [SQL Server 2025 Release Notes](https://learn.microsoft.com/en-us/sql/sql-server/sql-server-2025-release-notes?view=sql-server-ver17)
- [Editions and Supported Features](https://learn.microsoft.com/en-us/sql/sql-server/editions-and-components-of-sql-server-2025?view=sql-server-ver17)
