---
title: "Am Freitag startet Relationale Renaissance – SQL Server auf Deutsch"
date: 2026-08-06T01:07:00+02:00
slug: "start-relationale-renaissance-sql-server-auf-deutsch"
description: "Am 7. August startet meine neue deutschsprachige Serie über SQL Server. Das erste große Thema ist die sichere Evolution von Datenbankschemata."
categories:
  - "Relationale Renaissance"
tags:
  - "SQL Server"
  - "SQL Server auf Deutsch"
  - "Schema Evolution"
  - "Datenbankdesign"
  - "Relationale Renaissance"
draft: false
---

# Am Freitag startet Relationale Renaissance – SQL Server auf Deutsch

Am kommenden Freitag, dem **7. August**, startet meine neue Serie:

## Relationale Renaissance – SQL Server auf Deutsch

Es ist die deutschsprachige Version meiner Reihe über relationale Datenbanken, Datenmodellierung und den bewussten Umgang mit SQL Server.

Ich möchte mich dabei nicht nur auf einzelne T-SQL-Befehle konzentrieren.

Ich möchte auch darüber sprechen:

- warum bestimmte Lösungen funktionieren,
- welche Probleme sie lösen,
- welche Risiken sie mit sich bringen,
- wann sie sinnvoll sind,
- und wann eine einfachere Lösung besser ist.

Das erste große Thema der Serie lautet:

# Schema-Evolution in SQL Server

Ein Datenbankschema ist kein statisches Dokument.

Es verändert sich zusammen mit:

- der Anwendung,
- den Geschäftsprozessen,
- den Berichten,
- den Integrationen,
- und den Anforderungen der Benutzer.

Eine neue Spalte, eine Änderung des Datentyps oder die Aufteilung einer Tabelle in mehrere Tabellen können zunächst wie einfache technische Änderungen aussehen.

Das größte Risiko liegt jedoch meistens nicht in der Syntax von:

```sql
ALTER TABLE
```

Das eigentliche Problem besteht darin, dass wir einen Vertrag verändern, der von vielen verschiedenen Komponenten verwendet werden kann.

Zum Beispiel von:

- Anwendungen,
- gespeicherten Prozeduren,
- ETL-Prozessen,
- Berichten,
- Power-BI-Modellen,
- externen Integrationen,
- oder alten Skripten, an die sich niemand mehr erinnert.

Deshalb sollte die Evolution eines Datenbankschemas als kontrollierter Prozess behandelt werden und nicht als einzelne DDL-Anweisung.

## Acht praktische Muster

In dieser Serie werde ich acht Muster vorstellen, die dabei helfen, Schemaänderungen sicher und kontrolliert durchzuführen.

### 1. Expand–Migrate–Contract

Zuerst erweitern wir das Modell.

Danach migrieren wir die Daten und den Anwendungsverkehr.

Erst am Ende entfernen wir die alte Struktur.

### 2. Dual Write

Während einer Übergangsphase schreiben wir gleichzeitig in das alte und das neue Datenmodell.

Dabei sprechen wir über Atomarität, Idempotenz und die Frage nach der tatsächlichen Quelle der Wahrheit.

### 3. Shadow Column

Wir erstellen eine neue Spalte neben der alten, anstatt sofort eine riskante Änderung des Datentyps durchzuführen.

### 4. Backfill in Batches

Wir migrieren historische Daten in kleinen Paketen.

Dadurch reduzieren wir Sperren, das Wachstum des Transaktionslogs und die Kosten eines möglichen Rollbacks.

### 5. Compatibility View

Wir erstellen eine Kompatibilitätsschicht für Berichte und Integrationen, die weiterhin das alte Datenformat erwarten.

### 6. Parallel Table

Wir bauen eine vollständige Tabelle V2 neben der Tabelle V1 auf.

Danach synchronisieren wir die Daten, validieren beide Modelle und schalten erst anschließend den Datenverkehr um.

### 7. Blue-Green Database Deployment

Wir untersuchen, warum das Blue-Green-Verfahren bei Datenbanken deutlich schwieriger ist als bei zustandslosen Anwendungen.

### 8. Feature Flag for Schema Change

Wir trennen den Zeitpunkt der Codebereitstellung vom Zeitpunkt der Aktivierung eines neuen Lese- oder Schreibpfads.

## Die erste Folge

Die erste Folge wird eine Einführung in die gesamte Serie sein.

Ich stelle alle acht Muster vor und erkläre, welche Probleme sie lösen.

Danach erhält jedes Muster eine eigene Folge mit:

- einem geschäftlichen Beispiel,
- einem Datenmodell,
- einem praktischen SQL-Demo,
- einer Validierung,
- einer Besprechung der Kosten,
- und einer Erklärung, wann das Muster nicht verwendet werden sollte.

Die wichtigste Aussage der gesamten Serie lautet:

> Sichere Schema-Evolution bedeutet, die Übergangsphase zwischen dem alten und dem neuen Datenmodell kontrolliert zu gestalten.

Nicht nur der Zielzustand ist wichtig.

Der Weg dorthin ist genauso wichtig.

## Warum auf Deutsch?

Deutsch ist nicht meine Muttersprache.

Ich werde nicht immer vollkommen fehlerfrei sprechen und wahrscheinlich muss ich meine Aussprache oder einzelne Formulierungen manchmal korrigieren.

Ich möchte jedoch nicht auf den Moment warten, in dem alles perfekt ist.

Ich möchte beginnen, meine Sprachkenntnisse mit jeder neuen Folge verbessern und gleichzeitig praktisches Wissen über SQL Server weitergeben.

Denn Entwicklung beginnt nicht immer dann, wenn wir vollständig bereit sind.

Manchmal beginnt sie in dem Moment, in dem wir uns entscheiden, trotz unserer Unvollkommenheit den ersten Schritt zu machen.

## Start am 7. August

Die erste Folge der Serie:

**Relationale Renaissance – SQL Server auf Deutsch**

erscheint am Freitag, dem **7. August**.

Es wird technisch, praktisch und ohne die Illusion, dass sich jede Datenbankänderung mit einem einzigen `ALTER TABLE` erledigen lässt.

Bis Freitag.
