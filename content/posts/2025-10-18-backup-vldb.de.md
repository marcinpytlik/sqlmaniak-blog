---
title: "VLDB-Backup über 4 TB — So vermeidest du die Falle"
date: 2025-10-18
slug: backup-vldb
tags: [SQLServer, Backup, Restore, HighAvailability, DBA]
draft: false
---

Bei einer kleinen Datenbank wirkt ein Backup wie ein einfacher Knopfdruck. Bei einer Datenbank mit 4 TB oder mehr wird daraus eine Strategie.

SQL Server kann sehr große Datenbanken sichern. Die praktischen Grenzen liegen jedoch in der Infrastruktur: I/O, Netzwerk, Storage und manchmal in der falschen Annahme, dass ein abgeschlossenes Backup die Wiederherstellung garantiert.

Bei Very Large Databases (VLDBs) ist Backup ein **logistischer Prozess**. Er verlangt Planung, Tests, Segmentierung und eine nüchterne Berechnung: *Wie viele Daten, in welcher Zeit, wohin und für welches Wiederherstellungsziel?*

## 1. Striped Backup — Kein Luxus

Ein 4-TB-Backup in einer einzigen Datei kann zum betrieblichen Engpass werden. Verteile das Backup auf mehrere Stripes, möglichst auf unabhängige Storage-Ressourcen:

```sql
BACKUP DATABASE ERPCS_PROD
TO
    DISK = 'X:\Backups\ERPCS_PROD_1.bak',
    DISK = 'Y:\Backups\ERPCS_PROD_2.bak',
    DISK = 'Z:\Backups\ERPCS_PROD_3.bak',
    DISK = 'W:\Backups\ERPCS_PROD_4.bak'
WITH
    COMPRESSION,
    CHECKSUM,
    STATS = 5,
    MAXTRANSFERSIZE = 4194304,
    BUFFERCOUNT = 384;
```

Striping ermöglicht parallele Schreibvorgänge und kann die I/O-Last verteilen. Je nach Storage und Komprimierung kann der Unterschied erheblich sein. Der Vergleich von sechs Stunden mit 50 Minuten ist jedoch nur ein Beispielszenario, kein garantiertes Ergebnis.

## 2. Filegroup-Backup — Sichern, was sich ändert

Ein tägliches vollständiges VLDB-Backup kann unpraktisch sein. Wenn die Datenbank logisch in aktuelle, Reporting- und Archiv-Filegroups aufgeteilt ist, kommen Partial- oder Filegroup-Backups infrage:

```sql
BACKUP DATABASE ERP_DB FILEGROUP = 'FG_ACTIVE' 
TO DISK = 'X:\Backups\ERP_DB_FG_ACTIVE.bak' 
WITH COMPRESSION, CHECKSUM;
```

Dadurch lässt sich das Sicherungsvolumen aktiver Datenbereiche reduzieren. Filegroup-Backups erfordern allerdings eine sorgfältig geplante Restore-Sequenz und passende Logbackups. Ein Backup nur der aktiven Filegroup garantiert keine vollständige Wiederherstellbarkeit.

## 3. Restore-Test — Der häufig vergessene Schritt

Ein Backup, das nie wiederhergestellt wurde, ist zunächst nur eine unbewiesene Binärdatei.

VLDB-Restores benötigen ausreichend Kapazität, Zeit, dokumentierte Verfahren und realistische Wiederherstellungspläne. Teste auf einer anderen Instanz, passe Dateipfade an, miss die Dauer und dokumentiere die Ergebnisse.

Erst dann gibt es belastbare Hinweise, dass die Sicherung verwendbar ist.

## 4. Differential- und Logbackups — Ein praktikabler Kompromiss

Eine mögliche Strategie besteht aus einem wöchentlichen Full Backup, täglichen Differential-Backups und stündlichen oder häufigeren Transaktionslogbackups. Der tatsächliche Zeitplan muss sich nach RPO und RTO richten.

Im Recovery-Modell FULL oder BULK_LOGGED sind Logbackups für die Logkette und — soweit unterstützt — für Point-in-Time-Recovery entscheidend. Wiederherstellungspunkt und Optionen hängen vom Recovery-Modell und den durchgeführten Operationen ab.

## 5. Komprimierung und Deduplizierung

SQL Server Backup Compression kann die Backupgröße je nach Daten erheblich verringern. Eine Reduzierung um 70 % ist bei bestimmten Daten möglich, aber keineswegs allgemein zu erwarten.

Bei 24 TB kann das deutlich weniger Speicher- und Übertragungsvolumen bedeuten. Deduplizierende Backupsysteme wie Veeam, Commvault und Rubrik können je nach Workload und Architektur weitere Einsparungen bringen.

## 6. Aufbewahrung und Rotation

VLDB-Backup-Archive können schnell Hunderte Terabyte erreichen. Definiere eine Aufbewahrungsrichtlinie, etwa 14 Tage online, 30 Tage offline und ein Jahr im WORM-Speicher — sofern dies Compliance- und Recovery-Anforderungen erfüllt.

Beispiel für einen Cleanup-Aufruf:

```sql
EXECUTE dbo.usp_CleanupOldBackups 
    @Path = 'X:\Backups\', 
    @RetentionDays = 14;
```

**Wichtig:** `dbo.usp_CleanupOldBackups` ist eine benutzerdefinierte Prozedur, keine integrierte SQL-Server-Prozedur. Sie muss existieren und vor der Ausführung geprüft werden.

## 7. Monitoring und Alerts

Überwache Backup-Erfolg, Dauer und Alter. Nutze `msdb.dbo.backupset` als eine Datenquelle, beispielsweise mit Telegraf, InfluxDB und Grafana. Alarme sollten bei fehlenden Backups oder unerwartet langer Laufzeit auslösen. Prüfe außerdem, ob Backupdateien zugänglich und wiederherstellbar sind.

## 8. Die Psychologie des Backups

Die größten Fehler entstehen oft aus einem falschen Sicherheitsgefühl, nicht aus fehlerhafter T-SQL-Syntax. Ein Backup schafft nur Vertrauen, wenn die Wiederherstellung **getestet, wiederholbar und messbar** ist.

> Du hast erst dann wirklich ein Backup, wenn du es wiederhergestellt hast.

## 9. Beispielskripte und Konfiguration

Mein Repository enthält Materialien für VLDB-Backupstrategien mit SQL Server 2022: T-SQL für Striped-, Full-, Differential- und Logbackups, PowerShell für Automatisierung und Aufbewahrung, Monitoring-Dashboards mit Telegraf und InfluxDB sowie eine Restore-Test-Checkliste.

[SQLManiak — Backup-&-Restore-Skripte auf GitHub](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/06-internals/Lab07_Backup_Restore_Perf)

---

Wenn ein Backup Stunden dauert, ist das allein nicht unbedingt ein Problem. Das eigentliche Problem beginnt, wenn du nicht weißt, **wie lange die Wiederherstellung dauern wird**.
