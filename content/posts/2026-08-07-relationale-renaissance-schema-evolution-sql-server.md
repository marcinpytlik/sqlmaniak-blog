---
title: "Relationale Renaissance startet: 8 Muster für sichere Schema-Evolution"
date: 2026-08-07T01:06:00+02:00
slug: "relationale-renaissance-schema-evolution-sql-server"
description: "Die neue deutschsprachige Serie Relationale Renaissance startet mit acht praktischen Mustern für sichere und kontrollierte Schemaänderungen in SQL Server."
categories:
  - "Relationale Renaissance"
tags:
  - "SQL Server"
  - "SQL Server auf Deutsch"
  - "Schema Evolution"
  - "Datenbankdesign"
  - "Datenmigration"
  - "Relationale Renaissance"
draft: false
---

# Relationale Renaissance startet: 8 Muster für sichere Schema-Evolution

Heute startet meine neue deutschsprachige Serie:

## Relationale Renaissance – SQL Server auf Deutsch

In der ersten Folge geht es um ein Thema, das in fast jedem langfristig entwickelten System früher oder später wichtig wird:

## Schema-Evolution in SQL Server

Ein Datenbankschema ist kein statisches Dokument.

Es verändert sich zusammen mit:

- der Anwendung,
- den Geschäftsprozessen,
- den Berichten,
- den Integrationen,
- und den Anforderungen der Benutzer.

Neue Spalten werden benötigt.

Datentypen müssen verändert werden.

Eine Tabelle wird in mehrere Tabellen aufgeteilt.

Neue Beziehungen entstehen.

Alte Strukturen sollen entfernt werden.

Viele dieser Änderungen sehen auf den ersten Blick einfach aus.

Technisch scheint manchmal eine einzelne Anweisung zu genügen:

```sql
ALTER TABLE
```

Das größte Risiko liegt jedoch meistens nicht in der Syntax.

Das eigentliche Risiko entsteht dadurch, dass wir einen bestehenden Vertrag verändern.

Dieser Vertrag kann von vielen unterschiedlichen Komponenten verwendet werden:

- Anwendungen,
- gespeicherten Prozeduren,
- ETL-Prozessen,
- Berichten,
- Power-BI-Modellen,
- externen Schnittstellen,
- oder alten Skripten, an die sich niemand mehr erinnert.

Eine Schemaänderung kann technisch korrekt sein und trotzdem einen produktiven Prozess unterbrechen.

Deshalb sollten wir sie nicht als einzelne DDL-Anweisung betrachten.

Wir sollten sie als kontrollierten Übergang vom alten zum neuen Datenmodell planen.

## Acht praktische Muster

In der ersten Folge stelle ich acht Muster vor, die bei einer sicheren Schema-Evolution helfen.

### 1. Expand–Migrate–Contract

Zuerst erweitern wir das Modell.

Danach migrieren wir die Daten und den Anwendungsverkehr.

Erst wenn das neue Modell validiert wurde und die alte Struktur nicht mehr verwendet wird, beginnt die Aufräumphase.

### 2. Dual Write

Während einer Übergangsphase schreiben wir gleichzeitig in das alte und das neue Datenmodell.

Dabei müssen wir besonders auf Atomarität, Idempotenz, Fehlerbehandlung und eine klar definierte Quelle der Wahrheit achten.

### 3. Shadow Column

Anstatt eine bestehende Spalte sofort zu verändern, erstellen wir eine neue Spalte neben der alten.

Die Daten werden schrittweise migriert und die Anwendung wird kontrolliert auf die neue Spalte umgestellt.

### 4. Backfill in Batches

Historische Daten werden nicht in einer einzigen großen Transaktion aktualisiert.

Die Migration erfolgt in kleinen Paketen, um Sperren, das Wachstum des Transaktionslogs und die Kosten eines Rollbacks zu begrenzen.

### 5. Compatibility View

Ein View stellt das neue physische Datenmodell weiterhin in dem Format bereit, das alte Berichte oder Integrationen erwarten.

Dadurch erhalten wir Zeit für eine schrittweise Migration der abhängigen Systeme.

### 6. Parallel Table

Wir erstellen eine vollständige Tabelle V2 neben der bisherigen Tabelle V1.

Danach migrieren und synchronisieren wir die Daten, vergleichen beide Modelle und schalten den Datenverkehr erst nach erfolgreicher Validierung um.

### 7. Blue-Green Database Deployment

Blue-Green Deployment ist bei Datenbanken schwieriger als bei zustandslosen Anwendungen.

Nach der Umschaltung entstehen neue Daten. Deshalb ist ein Rollback nicht nur eine Änderung der Verbindungszeichenfolge, sondern auch eine Frage der Zustandssynchronisierung.

### 8. Feature Flag for Schema Change

Feature Flags trennen die Bereitstellung des Codes von der Aktivierung eines neuen Lese- oder Schreibpfads.

Dadurch kann eine neue Lösung zunächst für einen kleinen Teil des Verkehrs aktiviert und schrittweise erweitert werden.

## Die gemeinsame Frage hinter allen Mustern

Alle acht Muster beantworten ähnliche Fragen:

- Wie erhalten wir die Rückwärtskompatibilität?
- Wie migrieren wir historische Daten?
- Wie behandeln wir neue Schreibvorgänge während der Migration?
- Wie vergleichen wir das alte und das neue Modell?
- Wie erkennen wir weiterhin verwendete Abhängigkeiten?
- Wann ist ein Rollback noch möglich?
- Wann können temporäre Strukturen entfernt werden?

Das Ziel ist nicht, für jede Änderung dieselbe Lösung zu verwenden.

Das Ziel ist, einen Werkzeugkasten aufzubauen.

Für eine Änderung reicht vielleicht eine Shadow Column.

Eine andere benötigt einen Backfill in Batches.

Bei einer großen strukturellen Migration kann eine parallele Tabelle sinnvoller sein.

In komplexen Systemen werden häufig mehrere Muster miteinander kombiniert.

## Die wichtigste Aussage

> Sichere Schema-Evolution bedeutet, die Übergangsphase zwischen dem alten und dem neuen Datenmodell kontrolliert zu gestalten.

Nicht nur der Zielzustand ist wichtig.

Der Weg dorthin ist genauso wichtig.

## Die erste Folge ansehen

Die Einführung in die neue Serie ist jetzt auf YouTube verfügbar:

[SQL Server Schema-Evolution: 8 sichere Muster | Relationale Renaissance](https://youtu.be/HoKcOr0fstQ)

In den nächsten Folgen werde ich jedes Muster einzeln behandeln.

Zu jedem Thema plane ich:

- ein konkretes Problem,
- ein einfaches Datenmodell,
- ein praktisches SQL-Server-Demo,
- eine Validierung,
- die wichtigsten Risiken,
- und eine Erklärung, wann das Muster nicht verwendet werden sollte.

Deutsch ist nicht meine Muttersprache.

Ich werde deshalb nicht immer vollkommen fehlerfrei sprechen.

Ich möchte aber nicht warten, bis alles perfekt ist.

Ich möchte lernen, erklären und mich mit jeder neuen Folge weiterentwickeln.

Die erste Folge ist der Anfang dieses Weges.

Viel Spaß beim Anschauen.
