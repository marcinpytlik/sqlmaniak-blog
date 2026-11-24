---
title: "SQL-Server-Schemaentwicklung — Eine Reihe praktischer Muster"
date: 2026-08-05T00:01:00+02:00
slug: "ewolucja-schematu-sql-server-wzorce"
description: "Überblick über sichere Muster zur Schemaentwicklung: Expand–Contract, Dual Write, Shadow Column, Backfill, Kompatibilitätsviews, Parallel Table, Blue-Green und Feature Flags."
categories: "Relacyjny Renesans"
tags: [SQL Server,schema evolution,projektowanie baz danych,migracja danych]
draft: false
---

# SQL-Server-Schemaentwicklung — Eine Reihe praktischer Muster

Ein Datenbankschema ist kein statisches Dokument. Es entwickelt sich gemeinsam mit der Anwendung, den Geschäftsprozessen, Berichten und Integrationen weiter.

Das größte Risiko liegt meist nicht in der Syntax von `ALTER TABLE` selbst. Es entsteht dadurch, dass wir einen Vertrag ändern, auf den sich viele unabhängige Systemkomponenten verlassen.

Diese Serie stellt acht Muster vor, mit denen sich solche Änderungen kontrolliert durchführen lassen.

## 1. Expand–Migrate–Contract

Zuerst ergänzen wir die neue Struktur, anschließend migrieren wir Daten und Datenverkehr. Erst am Ende entfernen wir das alte Modell.

## 2. Dual Write

Vorübergehend wird in zwei Modelle geschrieben. Dafür sind Atomarität, Idempotenz und eine eindeutig definierte Quelle der Wahrheit erforderlich.

## 3. Shadow Column

Eine neue Spalte wird neben der alten angelegt. So lassen sich Datentyp oder Bedeutung der Daten sicher ändern.

## 4. Backfill in Batches

Die Datenmigration in kleinen Batches reduziert Sperren, das Wachstum des Transaktionslogs und die Kosten eines Rollbacks.

## 5. Compatibility View

Eine View stellt den alten Vertrag für Berichte und Integrationen bereit, obwohl das physische Modell bereits geändert wurde.

## 6. Parallel Table

Wir bauen eine vollständige V2-Tabelle neben V1 auf, synchronisieren und validieren die Daten und schalten anschließend den Datenverkehr um.

## 7. Blue-Green Database Deployment

Der Blue-Green-Ansatz erfordert bei Datenbanken besondere Vorsicht, da sie einen sich ständig ändernden Zustand speichern.

## 8. Feature Flag for Schema Change

Feature Flags trennen die Bereitstellung des Codes von der Aktivierung eines neuen Lese- oder Schreibpfads.

## Gemeinsames Prinzip

Jedes dieser Muster beantwortet ähnliche Fragen:

- Wie erhalten wir die Kompatibilität?
- Wie migrieren wir historische Daten?
- Wie behandeln wir Schreibvorgänge während der Migration?
- Wie überprüfen wir die Korrektheit?
- Wie stoppen wir eine Änderung oder machen sie rückgängig?
- Wann entfernen wir Übergangslösungen?

Ziel der Serie ist nicht, ein einziges universelles Rezept zu präsentieren. Vielmehr entsteht ein Werkzeugkasten, aus dem sich die passende Technik für Umfang und Risiko einer konkreten Änderung auswählen lässt.

Der wichtigste Gedanke der gesamten Serie lautet:

> Sichere Schemaentwicklung bedeutet, die Übergangsphase zwischen dem alten und dem neuen Modell zu kontrollieren.
