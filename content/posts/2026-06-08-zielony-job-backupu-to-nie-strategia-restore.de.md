---
title: "SQL Server Backup: Ein grüner Job ist noch keine Recovery-Strategie"
date: 2026-06-07T20:00:00+01:00
slug: sql-server-backup-zielony-job-to-nie-strategia-restore
description: "Ein erfolgreicher SQL-Server-Agent-Backupjob ist erst der Anfang. Eine echte Strategie ermöglicht die Wiederherstellung zum richtigen Zeitpunkt innerhalb der geforderten Zeit."
tags: [SQLServer, Backup, Restore, DBA, DisasterRecovery]
categories: [SQL Server]
draft: false
---

Ich kehre mit einem Thema zum Blog zurück, das in SQL Server auf den ersten Blick oft ganz einfach aussieht.

Backup.

In vielen Umgebungen endet die Diskussion über Datensicherheit mit einem Satz:

> Der Backupjob ist grün.

Das ist gut. Es bedeutet aber noch nicht, dass das Unternehmen eine echte Wiederherstellungsstrategie besitzt.

![SQL Server Backup und Restore — DBA-Paket](/images/sql-server-backup-restore-pakiet-dba-cover.png)

## Ein grüner Job bestätigt nur den Abschluss einer Operation

Ein grüner SQL-Server-Agent-Jobstatus bedeutet, dass eine bestimmte Operation erfolgreich abgeschlossen wurde. Das ist wichtig, sagt aber nur wenig aus.

Er verrät nicht, ob:

- die Backupdatei noch existiert,
- sie vom Zielserver für das Restore erreichbar ist,
- sie die richtige Datenbank enthält,
- eine vollständige LOG-Backupkette vorhanden ist,
- das TDE-Zertifikat und der private Schlüssel verfügbar sind,
- sich das Backup tatsächlich wiederherstellen lässt,
- die Wiederherstellungszeit das geforderte RTO erfüllt,
- der mögliche Datenverlust innerhalb des RPO vom Unternehmen akzeptiert wird.

Den Jobstatus zu überwachen reicht nicht.

## Backup ist nicht das Ziel

Ein Backup ist nur ein Mittel zum Zweck. Ziel ist die erfolgreiche Wiederherstellung nach einem Ausfall, Benutzerfehler, Datenbankschaden, Serververlust oder Sicherheitsvorfall.

Vergleiche diese Fragen:

```text
Czy backup się wykonał?
```

und:

```text
Czy potrafię odtworzyć bazę do właściwego punktu w czasie i w akceptowalnym czasie?
```

Die erste betrifft eine technische Operation. Die zweite betrifft die Verantwortung eines DBA.

## RPO und RTO müssen am Anfang stehen

Die Backupstrategie sollte aus zwei Kennzahlen abgeleitet werden:

- **RPO** — wie viel Datenverlust das Unternehmen maximal toleriert.
- **RTO** — wie schnell das System nach einem Ausfall wieder verfügbar sein muss.

Wenn maximal 15 Minuten Datenverlust akzeptabel sind, genügt ein tägliches LOG-Backup nicht. Muss das System innerhalb einer Stunde zurück sein, ein vollständiges Restore dauert aber sechs Stunden, erfüllt das bloße Vorhandensein eines Backups die Geschäftsanforderung nicht.

Hier beginnt die eigentliche Diskussion über die Strategie.

## Die Logkette — der stille Held der Wiederherstellung

Für Datenbanken im Recovery-Modell `FULL` oder `BULK_LOGGED` ist die LOG-Backupkette entscheidend.

Sie ermöglicht unter Berücksichtigung der Einschränkungen des Recovery-Modells die Wiederherstellung zu einem bestimmten Zeitpunkt.

Beispiel:

```text
20:00 FULL backup
22:00 DIFF backup
22:15 LOG backup
22:30 LOG backup
22:45 LOG backup
23:00 LOG backup
```

Soll die Datenbank auf 22:37 Uhr zurückgesetzt werden, reichen FULL und DIFF nicht. Wir benötigen den passenden Teil der Logkette und `STOPAT`.

Das Problem: Viele Administratoren prüfen, ob LOG-Backupjobs ausgeführt wurden, kontrollieren aber nicht die Kontinuität der Kette.

Eine einfache Prüfung der LOG-Backuphistorie:

```sql
DECLARE @DatabaseName sysname = N'ERP';

WITH LogBackups AS
(
    SELECT
        bs.database_name,
        bs.backup_start_date,
        bs.backup_finish_date,
        bs.first_lsn,
        bs.last_lsn,
        LAG(bs.last_lsn) OVER
        (
            PARTITION BY bs.database_name
            ORDER BY bs.backup_start_date
        ) AS previous_last_lsn
    FROM msdb.dbo.backupset AS bs
    WHERE bs.database_name = @DatabaseName
      AND bs.type = 'L'
)
SELECT
    database_name,
    backup_start_date,
    backup_finish_date,
    previous_last_lsn,
    first_lsn,
    last_lsn,
    CASE
        WHEN previous_last_lsn IS NULL THEN 'PIERWSZY LOG W WYNIKU'
        WHEN previous_last_lsn = first_lsn THEN 'OK - CIAGLOSC'
        ELSE 'UWAGA - PRZERWA W LANCUCHU'
    END AS log_chain_status
FROM LogBackups
ORDER BY backup_start_date;
```

Sie ersetzt keine vollständige Restore-Prozedur, kann aber potenzielle Probleme schnell sichtbar machen.

## TDE: Ein Datenbankbackup reicht manchmal nicht

Wenn die Datenbank TDE verwendet, genügt das Datenbankbackup allein möglicherweise nicht.

Zusätzlich brauchen wir:

- das TDE-Zertifikat,
- den privaten Schlüssel,
- das Passwort für das Zertifikatsbackup,
- einen sicheren Aufbewahrungsort,
- eine getestete Restore-Prozedur auf einer anderen Instanz.

Ohne TDE-Zertifikat kann das Backup zwar existieren, aber am benötigten Ort nicht wiederhergestellt werden.

Solche Probleme treten oft erst bei einem Ausfall oder DR-Test auf. Besser, wir entdecken sie beim Test.

## RESTORE VERIFYONLY ist kein Restore-Test

`RESTORE VERIFYONLY` ist nützlich, aber kein vollständiger Wiederherstellungstest.

Es kann Hinweise geben, dass das Backup lesbar erscheint, beantwortet jedoch nicht alle Fragen:

- Lässt sich die Datenbank vollständig wiederherstellen?
- Sind die Dateipfade korrekt?
- Sind alle Dateien eines Striped Backups vorhanden?
- Sind die TDE-Zertifikate verfügbar?
- Startet die Anwendung nach dem Restore?
- Läuft `DBCC CHECKDB` anschließend erfolgreich?
- Wie lange dauert die gesamte Prozedur tatsächlich?

Der echte Test eines Backups ist ein Restore-Test.

## Minimale DBA-Checkliste

Um zu beurteilen, ob Backups nur eine Operation oder Teil einer Strategie sind, beginne mit diesen Fragen:

- Kennen wir RPO und RTO für jede wichtige Datenbank?
- Wissen wir, welche Datenbanken `SIMPLE`, `FULL` oder `BULK_LOGGED` verwenden?
- Entspricht die Häufigkeit der LOG-Backups dem RPO?
- Prüfen wir die Kontinuität der Logkette?
- Führen wir regelmäßig Restore-Tests durch?
- Messen wir die Restore-Dauer und nicht nur die Backup-Dauer?
- Sichern wir Systemdatenbanken nach Konfigurationsänderungen?
- Haben wir Backups der TDE-Zertifikate?
- Gibt es eine Notfallprozedur bei Verlust von Server oder Storage?
- Kennt mehr als eine Person das Wiederherstellungsverfahren?

Wenn die Antwort meistens „Ich weiß es nicht“ lautet, funktionieren die Backups vielleicht, aber die Strategie muss verbessert werden.

## Warum ich darüber schreibe

Im Laufe der Jahre habe ich Umgebungen gesehen, in denen Backups formal vorhanden waren. Die Jobs waren grün, Dateien wurden erstellt, das Monitoring blieb ruhig.

Das Problem zeigte sich erst, als tatsächlich etwas wiederhergestellt werden musste.

Eine Datei fehlte. LOG-Backups fehlten. Das TDE-Zertifikat lag nur auf dem alten Server. Niemand wusste, welches DIFF das richtige war. Das Restore dauerte viel länger als erwartet. Die Anwendung funktionierte danach nicht, weil ein Teil der Daten außerhalb von SQL Server gespeichert war.

Deshalb wiederhole ich gerne:

> Entscheidend ist nicht, ob das Backup erfolgreich war.
> Entscheidend ist, ob das Restore gelingt.

## Zusätzliches Material

Auf Grundlage dieser Erfahrungen habe ich ein praktisches DBA-Paket erstellt:

**SQL Server Backup und Restore — DBA-Paket**

Es enthält:

- ein PDF-E-Book,
- T-SQL- und PowerShell-Skripte,
- DBA-Checklisten,
- Restore-Runbooks,
- Notfallverfahren,
- Material zu RPO, RTO, LSN, Logketten, TDE, gMSA, Backup-Monitoring und Restore-Tests.

Link zum Paket:

[SQL Server Backup und Restore — DBA-Paket](https://pytlik.gumroad.com/l/sql-server-backup-restore-pakiet-dba)

Hier geht es nicht darum, auf „Backup“ zu klicken. Es geht darum, Datenwiederherstellung in einer echten SQL-Server-Umgebung zu durchdenken.

---

Wenn du heute nur grüne Backupjobs hast, stelle dir eine Frage:

**Wann hast du zuletzt wirklich eine Datenbank aus einem Backup wiederhergestellt?**
