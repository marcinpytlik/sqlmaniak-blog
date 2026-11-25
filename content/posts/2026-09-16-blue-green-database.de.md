---
title: "Blue-Green Database Deployment: Warum Datenbanken schwieriger sind als Anwendungen"
date: 2026-09-16T00:01:00+02:00
slug: blue-green-database-deployment
description: "Blue-Green-Deployment für Datenbanken: Möglichkeiten und Grenzen der Analogie zur Anwendungsbereitstellung."
category: "Relationaler Renaissance"
tags: [SQL Server, blue green deployment, deployment, zero downtime, database DevOps]
draft: false
---

# Blue-Green Database Deployment: Warum Datenbanken schwieriger sind als Anwendungen

Blue-Green-Deployment für Anwendungen ist intuitiv:

- Blue bedient den produktiven Verkehr,
- Green erhält die neue Version,
- wir testen,
- schalten den Verkehr um,
- und kehren bei Problemen zu Blue zurück.

Bei Datenbanken ist das schwieriger, weil sie **veränderlichen Zustand** enthalten.

Sobald Benutzer nach dem Umschalten neue Daten in Green schreiben, ist Blue nicht mehr automatisch aktuell. Ein Rollback besteht nicht nur aus dem Wechsel des Endpunkts.

> Blue-Green für Datenbanken ist kein Problem des Kopierens von Schemas. Es geht um die Verantwortung für den Datenzustand und dessen Synchronisierung.

## Was kann Blue-Green bei einer Datenbank bedeuten?

Der Begriff kann verschiedene Lösungen beschreiben:

1. zwei vollständige Datenbanken,
2. zwei Schemas in einer Datenbank,
3. zwei Tabellenversionen,
4. eine Datenbank, die gleichzeitig mit Blue und Green kompatibel ist,
5. eine Replik, die für die Übernahme der aktiven Rolle vorbereitet ist.

Jede Variante hat andere Eigenschaften.

## Die sicherste Variante: Eine Datenbank, kompatibles Schema

Oft ist es am besten, die Datenbank nicht zu duplizieren. Stattdessen wird ein Schema vorbereitet, das mit beiden Anwendungsversionen kompatibel ist.

Reihenfolge:

1. additive Datenbankänderungen bereitstellen,
2. Green-Anwendung starten,
3. Green auf derselben Datenbank testen,
4. Verkehr umschalten,
5. Verhalten beobachten,
6. altes Schema bei einem späteren Deployment entfernen.

Dies kombiniert Blue-Green für Anwendungen mit dem Expand–Contract-Muster für Datenbanken.

## Zwei vollständige Datenbanken

Angenommen, wir haben:

```text
Sales_Blue
Sales_Green
```

Wir kopieren die Daten nach Green, stellen das neue Schema bereit und schalten die Anwendung um.

Das Problem: Was passiert mit Schreibvorgängen nach Beginn des Kopierens?

Wir benötigen Synchronisierung, beispielsweise durch:

- Replikation,
- CDC,
- Backup und Restore mit anschließendem Delta,
- Log Shipping,
- einen Anwendungsmechanismus,
- eine Ereigniswarteschlange.

Wenn die Synchronisierung nur in eine Richtung funktioniert, kann die Rückkehr nach dem Umschalten schwierig sein.

## Bidirektionale Synchronisierung

Sie klingt nach einer Rollback-Lösung, verursacht aber Konflikte:

- derselbe Datensatz wird in beiden Datenbanken geändert,
- unterschiedliche Reihenfolge von Operationen,
- abweichende Validierungsregeln,
- neue Felder nur in Green,
- Löschungen und Neuanlagen,
- Schlüsselkollisionen.

Bidirektionale Synchronisierung ist oft komplexer als die Migration selbst. Beide Umgebungen sollten nicht unabhängig voneinander Schreibvorgänge annehmen.

## Point of No Return

Jedes Deployment sollte einen **Point of No Return** definieren.

Davor ist die Rückkehr zu Blue ohne Datenverlust möglich. Danach kann ein Rollback erfordern:

- Rückmigration der Daten,
- Transformation neuer Werte,
- Nachspielen von Änderungen,
- Akzeptieren eingeschränkter Funktionalität.

Beispiel: Green speichert mehrere Kundenadressen, Blue unterstützt nur eine. Für die Rückkehr muss entschieden werden, welche Adresse erhalten bleibt. Das ist kein rein technisches Umschalten mehr.

## Verbindungen umschalten

Eine Anwendung kann Folgendes verwenden:

- DNS-Alias,
- Verbindungskonfiguration,
- Secret,
- Listener,
- Proxy-Schicht.

Bei einem Endpunktwechsel müssen Connection Pools berücksichtigt werden. Alte Verbindungen können noch eine Weile aktiv bleiben.

Einzuplanen sind:

- Schließen oder Aktualisieren von Connection Pools,
- laufende Transaktionen,
- Wiederholungsversuche,
- idempotente Schreibvorgänge,
- Monitoring der Verbindungen zu Blue und Green.

## Green testen

Tests auf einer Datenkopie sind wertvoll, aber schreibende Tests können Daten verändern. Erforderlich sind beispielsweise:

- isolierte Testkonten,
- markierte Datensätze,
- zurückgerollte Transaktionen,
- eigene Testkopien,
- synthetische Szenarien,
- Kontrolle asynchroner Nebenwirkungen.

Beim Testen von Green dürfen keine echten Nachrichten, Rechnungen oder Benachrichtigungen verschickt werden.

## Blue- und Green-Schemas in einer Datenbank

Man kann erstellen:

```text
blue.Orders
green.Orders
```

Das vereinfacht Teile der Synchronisierung und des Backups. Beide Versionen teilen jedoch:

- Instanzressourcen,
- Transaktionslog,
- Datenbankausfälle,
- Einstellungen,
- Teile der Sicherheitsgrenzen.

Es ist keine vollständige Isolation, kann aber für das unabhängige Umschalten einzelner Tabellen oder Module hilfreich sein.

## Observability

Nach dem Umschalten müssen wir messen:

- Verbindungen zu beiden Umgebungen,
- Anwendungsfehler,
- Antwortzeiten,
- Blocking und Deadlocks,
- Logwachstum,
- Synchronisierungsverzug,
- Unterschiede bei Zeilenzahlen,
- unbearbeitete Nachrichten,
- Abfragen auf das alte Schema.

Ein Rollback sollte auf konkreten Schwellenwerten beruhen und nicht auf einem allgemeinen Eindruck.

## Wann ist Blue-Green sinnvoll?

- die Anwendung kann unabhängig umgeschaltet werden,
- das Schema bleibt kompatibel,
- schneller Code-Rollback ist erforderlich,
- Datensynchronisierung ist klar definiert,
- der Point of No Return wurde bewusst geplant.

## Wann ist es zu teuer?

- die Datenbank ist sehr groß,
- hohe Schreiblast,
- keine Delta-Synchronisierung,
- neues Modell nicht rückwärtskompatibel,
- bidirektionale Schreibvorgänge erforderlich,
- keine Werkzeuge zur Zustandsvalidierung vorhanden.

## Zusammenfassung

Blue-Green Database Deployment ist keine einfache Übertragung des Anwendungsmusters.

Oft ist der sicherste Ansatz:

- Blue- und Green-Anwendungen,
- eine gemeinsame Datenbank,
- additives, mit beiden Versionen kompatibles Schema,
- spätere Contract-Phase.

Zwei vollständige Datenbanken können sinnvoll sein, verlangen aber Antworten zu Synchronisierung, Konflikten und Rückmigration.

Die wichtigste Erkenntnis:

> Code lässt sich in einer Sekunde umschalten. Den Datenzustand muss man bewusst durch die Änderung führen.
