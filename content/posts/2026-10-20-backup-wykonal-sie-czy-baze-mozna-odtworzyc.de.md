---
title: "Das Backup war erfolgreich. Lässt sich die Datenbank auch wiederherstellen?"
date: 2026-10-20T08:00:00+02:00
slug: backup-erfolgreich-ist-restore-moeglich
description: "Warum ein erfolgreiches Backup keinen erfolgreichen Restore garantiert: Restore-Tests, CHECKSUM, VERIFYONLY, TDE, RPO und RTO."
tags: [SQLServer, Backup, Restore, DisasterRecovery, DBA]
categories: [SQL Server]
draft: false
---

Der grüne Status eines Backup-Jobs beantwortet eine Frage:

> Wurde der Backup-Befehl erfolgreich ausgeführt?

Er beantwortet nicht die Frage:

> Können wir die Datenbank innerhalb der geforderten Zeit und bis zum richtigen Wiederherstellungspunkt wiederherstellen?

## Backup mit CHECKSUM

```sql
BACKUP DATABASE [TwojaBaza]
TO DISK = N'X:\Backup\TwojaBaza_FULL.bak'
WITH
    COMPRESSION,
    CHECKSUM,
    STATS = 10;
```

## RESTORE VERIFYONLY

```sql
RESTORE VERIFYONLY
FROM DISK = N'X:\Backup\TwojaBaza_FULL.bak'
WITH CHECKSUM;
```

Dieser Befehl ist nützlich. Er bestätigt jedoch weder die Vollständigkeit der Backup-Kette noch die Verfügbarkeit des TDE-Zertifikats, die Restore-Dauer oder die Funktionsfähigkeit der Anwendung.

## Vollständiger Restore-Test

```sql
RESTORE DATABASE [TwojaBaza_RestoreTest]
FROM DISK = N'X:\Backup\TwojaBaza_FULL.bak'
WITH
    MOVE N'TwojaBaza_Data'
        TO N'Y:\RestoreTest\TwojaBaza_RestoreTest.mdf',
    MOVE N'TwojaBaza_Log'
        TO N'Z:\RestoreTest\TwojaBaza_RestoreTest.ldf',
    RECOVERY,
    CHECKSUM,
    STATS = 10;
```

Nach der Wiederherstellung:

```sql
DBCC CHECKDB (N'TwojaBaza_RestoreTest')
WITH NO_INFOMSGS;
```

## TDE und Zertifikate

Das Backup einer verschlüsselten Datenbank kann gültig sein, sich aber ohne Zertifikat und privaten Schlüssel nicht wiederherstellen lassen.

Ein Disaster-Recovery-Plan sollte Export, sichere Aufbewahrung und einen Importtest umfassen.

## RPO und RTO

Das RPO legt den maximal akzeptablen Datenverlust fest.

Das RTO legt die maximal akzeptable Dauer bis zur Wiederaufnahme des Betriebs fest.

Ein Backup kann technisch korrekt sein, während die gesamte Strategie die Anforderungen trotzdem verfehlt.

## Was sollte man beim Test messen?

- Zeit zum Auffinden der Dateien,
- Kopierdauer,
- Restore-Dauer,
- Recovery-Dauer,
- Laufzeit von `DBCC CHECKDB`,
- Dauer des Anwendungstests,
- Gesamtdauer der Prozedur.

## Fazit

Ein Backup allein ist kein Nachweis der Wiederherstellungsbereitschaft.

Erst ein getesteter Restore liefert diesen Nachweis.

Ein besonnener DBA weist regelmäßig nach, dass sich Daten innerhalb der vorgegebenen RPO- und RTO-Ziele wiederherstellen lassen.