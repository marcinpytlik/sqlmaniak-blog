---
title: "VLDB-Backups über 4 TB — So vermeidest du die Fallen"
date: 2025-10-18
slug: backup-vldb
tags: [SQLServer, Backup, Restore, HighAvailability, DBA]
draft: false
---

Bei kleinen Datenbanken wirkt ein Backup wie ein einfacher Knopfdruck. Ab 4 TB ist es eine Strategie.

SQL Server kann sehr große Datenbanken sichern. Die Grenzen setzt jedoch oft die Infrastruktur: I/O, Netzwerk, Storage-Kapazität und manchmal die falsche Annahme, dass ein erfolgreiches Backup eine erfolgreiche Wiederherstellung garantiert.

In der Welt der **Very Large Databases (VLDBs)** ist Backup ein logistischer Prozess. Er erfordert Planung, Tests, Segmentierung und klare Berechnungen: wie viele Daten, wie schnell, wohin und wozu?

## 1. Striped Backup — kein Luxus

Ein 4-TB-Backup in einer einzigen Datei birgt operative Risiken. Teile es in mehrere Stripes auf, idealerweise auf unabhängige Storage-Ressourcen:

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

Striping verteilt die Last und erlaubt parallele Schreibvorgänge. Je nach Umgebung kann dies die Backupdauer erheblich reduzieren. Das Beispiel von sechs Stunden gegenüber fünfzig Minuten ist eine Illustration, keine Leistungsgarantie.

## 2. Filegroup-Backup — sichern, was sich ändert

Bei VLDBs kann ein tägliches Full Backup unnötig teuer sein. Wenn historische, Reporting- und aktuelle Daten getrennt sind, kommen **Partial Backups** oder **Filegroup-Backups** infrage:

```sql
BACKUP DATABASE ERP_DB FILEGROUP = 'FG_ACTIVE' 
TO DISK = 'X:\Backups\ERP_DB_FG_ACTIVE.bak' 
WITH COMPRESSION, CHECKSUM;
```

Damit lässt sich das Backupvolumen aktiver Filegroups reduzieren. Allerdings wird die Restore-Strategie komplexer: Prüfe Filegroup-Abhängigkeiten, Recovery-Modell, Logbackups und Wiederherstellbarkeit.

## 3. Restore-Test — der häufig vergessene Schritt

Ein Backup, das nie wiederhergestellt wurde, ist nur eine Binärdatei mit ungeprüfter Wiederherstellbarkeit.

Das Restore einer VLDB benötigt Platz, Zeit, Verfahren und eine sorgfältig geplante Restore-Reihenfolge.

Teste es:

- Stelle das Backup auf einer anderen Instanz wieder her.
- Passe die Dateipfade an.
- Miss und dokumentiere die Recovery-Dauer.

Erst dann kannst du beurteilen, ob das Backup die Recovery-Ziele erfüllt.

## 4. DIFF + LOG — ein praktikabler Kompromiss

Eine mögliche Strategie ist ein wöchentliches Full Backup, tägliche Differential Backups und stündliche oder häufigere Transaktionslogbackups.

Bei VLDBs muss sich der Zeitplan nach **RPO und RTO** richten, nicht nach einer universellen Regel.

Im Recovery-Modell `FULL` sind Logbackups entscheidend, um eine wiederherstellbare Logkette und Point-in-Time-Recovery zu ermöglichen.

## 5. Kompression und Deduplizierung

SQL Server Backup Compression kann die Ausgabe erheblich reduzieren. Bei manchen Daten nähert sich die Reduktion 70 %, der tatsächliche Faktor hängt jedoch von den Daten ab.

Bei einem hypothetischen 24-TB-Backup kann eine hohe Kompressionsrate Storage- und Transferbedarf stark verringern.

Backuplösungen wie Veeam, Commvault und Rubrik können zusätzliche Deduplizierung ermöglichen.

## 6. Retention und Rotation

VLDB-Backups können schnell Hunderte Terabyte belegen. Definiere eine Aufbewahrungsrichtlinie, beispielsweise 14 Tage online, 30 Tage offline und ein Jahr im WORM-Archiv, wenn die Richtlinien dies verlangen.

Automatisiere die Bereinigung alter Backups:

```sql
EXECUTE dbo.usp_CleanupOldBackups 
    @Path = 'X:\Backups\', 
    @RetentionDays = 14;
```

**Hinweis:** `dbo.usp_CleanupOldBackups` ist hier eine benutzerdefinierte Prozedur, keine integrierte SQL-Server-Stored-Procedure. Sie muss vor der Nutzung implementiert und getestet werden.

## 7. Monitoring und Alerts

Jedes Backup benötigt ein dokumentiertes Ergebnis und eine Laufzeit. Überwache `msdb.dbo.backupset`, etwa mit Telegraf, InfluxDB und Grafana.

Alarmiere bei ungewöhnlich langen Backups oder wenn ein erwarteter Backupdatensatz fehlt.

## 8. Die Psychologie des Backups

Auch erfahrene DBAs scheitern manchmal nicht an T-SQL, sondern an falscher Sicherheit.

Ein Backup gibt nur dann Sicherheit, wenn es **getestet, wiederholbar und messbar** ist.

> „Du hast erst dann wirklich ein Backup, wenn du es wiederhergestellt hast.“

Das gilt auch, wenn die Datenbank schneller wächst als das Storage-Array.

## 9. Beispielskripte und Konfiguration

Im Repository gibt es Materialien für VLDB-Backupstrategien mit SQL Server 2022:

- **T-SQL-Skripte** für Striped-, Full-, Differential- und Logbackups.
- **PowerShell** für Automatisierung und Aufbewahrung.
- **Telegraf + InfluxDB**-Dashboards für das Monitoring.
- **Restore-Test-Checklisten**.

[SQLManiak — Backup & Restore Scripts (GitHub)](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/06-internals/Lab07_Backup_Restore_Perf)

---

Ein stundenlanges Backup ist nicht unbedingt das Problem. Das eigentliche Problem beginnt, wenn du nicht weißt, **wie lange die Wiederherstellung dauert**.
