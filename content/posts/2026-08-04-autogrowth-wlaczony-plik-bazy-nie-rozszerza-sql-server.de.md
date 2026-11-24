---
title: "Autogrowth ist aktiviert, aber die Datenbankdatei wächst trotzdem nicht. Warum?"
date: 2026-08-04
slug: autogrowth-wlaczony-plik-bazy-nie-rozszerza-sql-server
description: "Warum SQL-Server-Autogrowth trotz Aktivierung scheitern kann: Dateigrenzen, Speicherplatz, Storage-Limits, Diagnoseabfragen und DBA-Best-Practices."
tags: [SQLServer, Autogrowth, MDF, NDF, LDF, DBA, Troubleshooting]
categories: [SQL Server]
draft: false
---

Ein verbreitetes Missverständnis bei der SQL-Server-Administration lautet: **Autogrowth** einschalten, und alle Platzprobleme sind gelöst.

In der Praxis kann Autogrowth aktiviert und konfiguriert sein, während die Datenbank dennoch fehlenden Speicher meldet, die Anwendung Fehler ausgibt und die Datei nicht wächst.

Meist ist der Autogrowth-Mechanismus nicht defekt. SQL Server stößt vielmehr auf konfigurierte oder externe Grenzen.

Dieser Beitrag erklärt den Mechanismus, mögliche Fehlerursachen, die Diagnose von Daten- und Logdateien und sichere Einstellungen für Produktionsumgebungen.

## Was ist Autogrowth?

Autogrowth vergrößert Datenbankdateien automatisch, wenn zusätzlicher Platz benötigt wird. Eine Datendatei kann beispielsweise folgenden Zuwachs haben:

```text
1024 MB
```

Ist der freie Platz in der Datei erschöpft, versucht SQL Server, weitere 1 GB zuzuweisen.

Dafür braucht die Engine jedoch freien Speicher auf dem Datenträger, passende Berechtigungen, die Möglichkeit zur Dateivergrößerung, ein geeignetes `MAXSIZE` und funktionierendes Storage.

> Autogrowth schafft keinen neuen Speicherplatz. Es verwendet nur bereits vorhandenen Platz.

## Freier Platz innerhalb einer Datei und auf dem Datenträger

Das sind zwei unterschiedliche Größen.

Eine 100-GB-MDF- oder NDF-Datei kann nur 80 GB belegte Datenseiten enthalten. SQL Server nutzt die übrigen 20 GB, ohne die physische Datei zu vergrößern.

Ist die Datei fast voll, muss sie wachsen. Ist der Datenträger voll, scheitert das trotz aktiviertem Autogrowth.

Der Datenträger meldet möglicherweise:

```text
Free space: 0 MB
```

## Größe der Datenbankdateien prüfen

Verwende `sys.database_files`:

```sql
SELECT
    name AS LogicalFileName,
    type_desc AS FileType,
    physical_name AS PhysicalFileName,
    size / 128.0 AS FileSizeMB,
    max_size,
    growth,
    is_percent_growth
FROM sys.database_files;
```

Die Abfrage zeigt logische und physische Namen, Dateitypen, Größen sowie `max_size`, `growth` und `is_percent_growth`.

Achte besonders auf:

```text
max_size
growth
is_percent_growth
```

## Autogrowth-Konfiguration verstehen

Wenn:

```text
is_percent_growth = 0
```

wird `growth` in 8-KB-Seiten gespeichert. Umrechnung in MB:

```sql
SELECT
    name,
    growth / 128.0 AS GrowthMB
FROM sys.database_files
WHERE is_percent_growth = 0;
```

Wenn:

```text
is_percent_growth = 1
```

ist `growth` ein Prozentwert. Beispielsweise:

```text
growth = 10
```

bedeutet 10 % Wachstum. Feste Zuwachswerte sind in Produktion meist besser vorhersehbar, zum Beispiel:

```text
512 MB
1024 MB
4096 MB
```

10 % von 10 GB entsprechen ungefähr 1 GB; 10 % von 1 TB dagegen ungefähr 100 GB.

## Belegung von Datendateien prüfen

Für Datendateien verwende `FILEPROPERTY`:

```sql
SELECT
    df.name AS LogicalFileName,
    df.type_desc AS FileType,
    df.physical_name,
    df.size / 128.0 AS FileSizeMB,
    FILEPROPERTY(df.name, 'SpaceUsed') / 128.0 AS UsedSpaceMB,
    (
        df.size -
        FILEPROPERTY(df.name, 'SpaceUsed')
    ) / 128.0 AS FreeSpaceMB,
    CAST(
        100.0 * FILEPROPERTY(df.name, 'SpaceUsed') / NULLIF(df.size, 0)
        AS decimal(10,2)
    ) AS UsedPercent
FROM sys.database_files AS df
WHERE df.type = 0;
```

Die Abfrage liefert Dateigröße, belegten und freien Platz sowie den Belegungsgrad. Wenig `FreeSpaceMB` bedeutet, dass die Datei bald wachsen muss — nicht aber, dass das Volume genügend Platz hat.

## Freien Speicher auf Volumes prüfen

Verwende `sys.dm_os_volume_stats`:

```sql
SELECT DISTINCT
    vs.volume_mount_point,
    vs.logical_volume_name,
    vs.total_bytes / 1024.0 / 1024 / 1024 AS TotalSizeGB,
    vs.available_bytes / 1024.0 / 1024 / 1024 AS FreeSpaceGB,
    CAST(
        100.0 * vs.available_bytes / NULLIF(vs.total_bytes, 0)
        AS decimal(10,2)
    ) AS FreeSpacePercent
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats(mf.database_id, mf.file_id) AS vs
ORDER BY vs.volume_mount_point;
```

Diese Prüfung ist besonders wichtig, wenn Autogrowth scheitert. Ohne ausreichend freien Platz kann die Datei nicht wachsen.

## Sieben häufige Ursachen für fehlgeschlagenes Wachstum

### 1. Zu wenig freier Speicher auf dem Datenträger

Autogrowth ist erlaubt, aber der Datenträger ist voll. SQL Server kann melden:

```text
Could not allocate space for object
because the filegroup is full.
```

oder:

```text
Autogrow of file failed because
there is insufficient disk space.
```

Mögliche Maßnahmen: Platz freigeben, Volume erweitern, Dateien mit einem unterstützten Verfahren verschieben, eine Datei zur gleichen Filegroup hinzufügen oder unnötige Nicht-Datenbankdateien entfernen.

MDF-, NDF- und LDF-Dateien niemals manuell im Betriebssystem löschen.

### 2. Maximale Dateigröße erreicht

Eine Datei kann Autogrowth aktiviert haben und trotzdem durch `MAXSIZE` begrenzt sein:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Data',
    MAXSIZE = 100GB
);
```

Bei 100 GB wächst sie nicht weiter. Grenze prüfen:

```sql
SELECT
    name,
    size / 128.0 AS CurrentSizeMB,
    CASE
        WHEN max_size = -1 THEN 'UNLIMITED'
        ELSE CAST(max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB
FROM sys.database_files;
```

Der Wert:

```text
max_size = -1
```

bedeutet kein SQL-Server-Dateilimit, aber keineswegs unbegrenzten Speicherplatz.

### 3. Die Filegroup ist voll

Eine Datenbank kann mehrere Filegroups besitzen. Tabellen und Indizes gehören zu bestimmten Filegroups. Freier Platz in einer anderen Filegroup steht nicht automatisch zur Verfügung.

Zuordnung prüfen:

```sql
SELECT
    fg.name AS FilegroupName,
    df.name AS LogicalFileName,
    df.physical_name,
    df.size / 128.0 AS FileSizeMB,
    CASE
        WHEN df.max_size = -1 THEN 'UNLIMITED'
        ELSE CAST(df.max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB
FROM sys.filegroups AS fg
INNER JOIN sys.database_files AS df
    ON fg.data_space_id = df.data_space_id
ORDER BY
    fg.name,
    df.name;
```

Mögliche Maßnahmen: bestehende Datei vergrößern, Datei zur selben Filegroup hinzufügen, Objekt verschieben oder Daten archivieren.

### 4. Der Zuwachs ist größer als der freie Speicher

Angenommen, auf dem Datenträger sind noch 800 MB frei, aber die Datei soll wachsen um:

```text
1024 MB
```

Die angeforderten 1 GB können nicht zugewiesen werden. Ein kleinerer Zuwachs kann kurzfristig helfen, ersetzt aber keine Kapazitätsplanung.

### 5. Das Problem betrifft das Transaktionslog

Daten- und Logdateien funktionieren unterschiedlich. Bei vollem Log kann eine Logtrunkierung oder die Beseitigung einer Wiederverwendungssperre wichtiger sein als zusätzlicher Platz.

Prüfe:

```sql
SELECT
    name,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE name = DB_NAME();
```

`log_reuse_wait_desc` kann Folgendes anzeigen:

```text
LOG_BACKUP
ACTIVE_TRANSACTION
AVAILABILITY_REPLICA
REPLICATION
CHECKPOINT
```

Im Recovery-Modell `FULL` sollten regelmäßige Transaktionslogbackups überprüft werden. Eine bloße Vergrößerung des Logs verschiebt das nächste Problem möglicherweise nur.

### 6. Berechtigungen des SQL-Server-Dienstkontos

SQL Server läuft unter einem Dienstkonto, Domänenkonto oder gMSA. Das Konto benötigt passende Dateisystemberechtigungen. Nach Datei- oder NTFS-Änderungen kann das Wachstum scheitern.

Prüfe Dienstidentität, NTFS-Berechtigungen, SQL Server Error Log und Windows-Ereignisprotokoll.

### 7. Zusätzliche Dateisystem- oder Storage-Grenzen

Ein Windows-Volume kann freien Platz melden, obwohl der Hypervisor-Datastore, Thin-Provisioning-Speicher, eine Netzwerkfreigabe, Quota oder LUN an ihre Grenzen stoßen.

Solche Fälle erfordern oft die Zusammenarbeit mit Storage-, Virtualisierungs- und Betriebssystemadministratoren.

## Autogrowth-Fehler finden

Beginne im SQL Server Error Log:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'Autogrow';
```

Suche außerdem nach Allokationsfehlern:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'Could not allocate space';
```

und:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'insufficient disk space';
```

Extended Events helfen, Wachstumsvorgänge und deren Dauer zu überwachen.

## Ist Autogrowth eine Kapazitätsstrategie?

Nein. Autogrowth ist eine Sicherheitsreserve, nicht die wichtigste Methode zur Größenverwaltung.

Dimensioniere Dateien vorausschauend, beobachte Wachstumstrends, setze Alerts, halte Reserven vor und vergrößere Dateien rechtzeitig vor erwarteter Last.

Wenn eine Datenbank täglich automatisch wächst, muss die Kapazitätsplanung wahrscheinlich verbessert werden.

## Warum ist häufiges Autogrowth problematisch?

Jedes Dateiwachstum kann Verzögerungen verursachen.

Bei Datendateien kann Instant File Initialization (IFI) den Aufwand deutlich reduzieren, sofern unterstützt und aktiviert. Logdateiwachstum benötigt normalerweise eine Initialisierung; neuere SQL-Server-Versionen unterstützen jedoch begrenzte Instant Log Initialization für bestimmte kleine Wachstumsvorgänge. Prüfe das Verhalten für deinen Build.

Sehr kleine Logzuwächse können zu vielen VLFs und zusätzlichem Aufwand führen. Sehr große Zuwächse können deutliche Pausen verursachen. Wähle Werte passend zu Workload und Storage.

## Beispielkonfiguration

Datendatei:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Data',
    FILEGROWTH = 1024MB
);
```

Logdatei:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Log',
    FILEGROWTH = 512MB
);
```

Einen universellen Wert gibt es nicht. Entscheidend sind Datenbankgröße, Wachstumsrate, Last, akzeptable Dauer des Wachstums, Storage-Performance, Recovery-Modell und Häufigkeit der Logbackups.

## Zusammengefasste Diagnoseabfrage

Dateien der aktuellen Datenbank prüfen:

```sql
SELECT
    DB_NAME() AS DatabaseName,
    df.file_id AS FileId,
    df.name AS LogicalFileName,
    df.type_desc AS FileType,
    df.physical_name AS PhysicalFileName,
    df.size / 128.0 AS FileSizeMB,
    CASE
        WHEN df.type = 0
        THEN FILEPROPERTY(df.name, 'SpaceUsed') / 128.0
        ELSE NULL
    END AS UsedSpaceMB,
    CASE
        WHEN df.type = 0
        THEN
            (
                df.size -
                FILEPROPERTY(df.name, 'SpaceUsed')
            ) / 128.0
        ELSE NULL
    END AS FreeSpaceMB,
    CASE
        WHEN df.max_size = -1
        THEN 'UNLIMITED'
        ELSE CAST(df.max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB,
    CASE
        WHEN df.is_percent_growth = 1
        THEN CAST(df.growth AS varchar(20)) + '%'
        ELSE CAST(df.growth / 128.0 AS varchar(20)) + ' MB'
    END AS Autogrowth
FROM sys.database_files AS df
ORDER BY df.file_id;
```

Mit freiem Volume-Speicher kombinieren:

```sql
SELECT DISTINCT
    DB_NAME(mf.database_id) AS DatabaseName,
    mf.name AS LogicalFileName,
    mf.physical_name,
    vs.volume_mount_point,
    vs.total_bytes / 1024.0 / 1024 / 1024 AS TotalSizeGB,
    vs.available_bytes / 1024.0 / 1024 / 1024 AS FreeSpaceGB,
    CAST(
        100.0 * vs.available_bytes /
        NULLIF(vs.total_bytes, 0)
        AS decimal(10,2)
    ) AS FreeSpacePercent
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats
(
    mf.database_id,
    mf.file_id
) AS vs
WHERE mf.database_id = DB_ID()
ORDER BY mf.file_id;
```

## Was tun bei 0 MB freiem Platz in der Datei?

1. Dateityp bestimmen: MDF, NDF oder LDF.
2. Internen freien Platz bei Datendateien mit `FILEPROPERTY` prüfen.
3. Datenträgerkapazität mit `sys.dm_os_volume_stats` prüfen.
4. `MAXSIZE` kontrollieren.
5. Zuwachs mit freiem Speicher vergleichen.
6. SQL Server Error Log lesen.
7. Bei Logdateien `log_reuse_wait_desc` prüfen.
8. Wachstumstrends und kürzliche Vorgänge wie Import, Index Rebuild, ETL oder große Transaktionen untersuchen.

## Was sollte man vermeiden?

Keine Datenbankdateien im Betriebssystem löschen, keinen Shrink ohne Ursachenanalyse durchführen, keine extrem kleinen Zuwächse konfigurieren, prozentuales Wachstum nicht unüberlegt einsetzen, Logs nicht ohne Prüfung der Wiederverwendungssperren vergrößern, `UNLIMITED` nicht mit unendlicher Kapazität verwechseln und wiederkehrendes Autogrowth nicht ignorieren.

Shrink ist ein Werkzeug für ausgewählte Ausnahmesituationen, nicht für die tägliche Speicherverwaltung.

## Vorbeugung

Überwache freien Volume-Speicher (Prozent und GB), freien Platz in Dateien, Anzahl und Dauer von Autogrowth-Ereignissen, Wachstumstrends, Loggröße, Wiederverwendungsgründe und Dateilimits.

Beispielhafte Alarmschwellen:

```text
poniżej 20% wolnego miejsca – ostrzeżenie,
poniżej 10% – alert krytyczny,
poniżej 5% – natychmiastowa reakcja.
```

Schwellen müssen auch die absolute Volume-Größe berücksichtigen: 10 % von 100 GB sind nur 10 GB, 10 % von 10 TB dagegen 1 TB.

## Zusammenfassung

Autogrowth garantiert nicht, dass eine Datei wachsen kann. Ursachen sind volle Datenträger, `MAXSIZE`, volle Filegroups, zu große Zuwachswerte, Berechtigungen, Storage-Limits oder blockierte Logwiederverwendung.

Unterscheide immer:

1. Physische Dateigröße.
2. Freier Platz innerhalb der Datei.
3. Freier Platz auf dem Datenträger.

Autogrowth ist ein Schutzmechanismus, kein Ersatz für Monitoring, Kapazitätsplanung und sinnvolle Dateigrößen.

Ein besonnener DBA beobachtet Trends, setzt Alerts und erweitert die Kapazität, bevor Platzmangel zum Produktionsvorfall wird.
