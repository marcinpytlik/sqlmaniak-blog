---
title: "PAGE Restore: Chirurgie an der Datenbank"
date: 2025-10-24
slug: page-restore
tags: [SQLServer, Backup, Restore, Internals, PageRestore]
draft: false
---

Wenn eine Datenbank Milliarden von Datenseiten enthält, wirkt ein vollständiger Restore wie eine Herztransplantation. Manchmal genügt jedoch ein präziser Eingriff: nur die beschädigte Seite wiederherzustellen. *PAGE Restore* ist die chirurgische Methode von SQL Server, um einen Teil zu reparieren, statt die gesamte Datenbank wiederherzustellen.

## 🧩 Die Idee

SQL Server speichert Daten in 8-KB-Seiten. Wird eine Seite durch einen I/O-Fehler, Datenträgerdefekt oder Prüfsummenfehler beschädigt, kann die Engine sie als verdächtig markieren. Unter geeigneten Bedingungen lässt sich **nur die betroffene Seite** aus einem Backup wiederherstellen, ohne die gesamte Datenbank oder Datendatei zurückzuspielen.

Das ist einer der präzisesten Mechanismen der **Wiederherstellungsinfrastruktur der Database Engine**.

## 🧠 Wann PAGE RESTORE möglich ist

✅ Die Datenbank muss das Wiederherstellungsmodell **FULL** oder **BULK_LOGGED** verwenden.

✅ Benötigt werden:
- Ein verwendbares **Full Backup** (gegebenenfalls zusätzlich ein Differential Backup).
- Die erforderlichen **Transaktionsprotokoll-Backups**, um die wiederhergestellte Seite auf den aktuellen Stand zu bringen.
- Die Kennungen der beschädigten Seiten (`file_id:page_id`).

## 🔍 Diagnose

```sql
-- sprawdź, które strony zostały oznaczone jako uszkodzone
SELECT database_id, file_id, page_id, event_type, error_count, last_update_date
FROM msdb.dbo.suspect_pages;
```

Die Werte von `event_type` umfassen:
- `1` — Fehler 823 (I/O).
- `2` — ungültige Prüfsumme.
- `3` — Torn Page.
- `4` — wiederhergestellt.
- `5` — freigegeben.
- `7` — ungültiger Header.

## 🧪 Labordemonstration

```sql
-- 1️⃣ Wymuszenie błędu (symulacja – nie rób w produkcji!)
DBCC WRITEPAGE ('AdventureWorks2022', 1, 200, 0, 1, 0x45, 1);

-- 2️⃣ Próba odczytu
DBCC CHECKDB('AdventureWorks2022') WITH NO_INFOMSGS, ALL_ERRORMSGS;
GO
SELECT * FROM msdb.dbo.suspect_pages;

-- 3️⃣ PAGE RESTORE – przywracamy tylko uszkodzoną stronę (1:200)
RESTORE DATABASE AdventureWorks2022
PAGE='1:200'
FROM DISK = 'D:\Backups\AdventureWorks2022_FULL.bak'
WITH NORECOVERY;
GO

-- 4️⃣ Odtwarzamy logi, by baza była spójna
RESTORE LOG AdventureWorks2022
FROM DISK = 'D:\Backups\AdventureWorks2022_LOG.trn'
WITH RECOVERY;
GO
```

> Ziel ist es, eine einzelne 8-KB-Seite wiederherzustellen und die Datenbank ohne vollständigen Datenbank-Restore in einen konsistenten Zustand zu bringen. Die tatsächlichen Schritte hängen vom Datenbankzustand und den verfügbaren Log-Backups ab.

**Warnung:** `DBCC WRITEPAGE` beschädigt absichtlich eine Seite. Verwende dieses Beispiel ausschließlich in einem isolierten, entbehrlichen Lab — niemals in der Produktion.

## 📊 Ergebnis prüfen

```sql
SELECT * FROM msdb.dbo.suspect_pages WHERE event_type = 4;
```

Ein Eintrag mit `event_type = 4` bedeutet, dass der Datensatz der verdächtigen Seite als wiederhergestellt markiert wurde.

## 🧰 Nützliche Diagnosewerkzeuge

| Werkzeug | Zweck |
|---|---|
| `DBCC CHECKDB` | Beschädigungen erkennen und melden. |
| `msdb.dbo.suspect_pages` | Ereignisse zu verdächtigen Seiten verfolgen. |
| `DBCC PAGE` | Einzelne Seiten untersuchen (Labordiagnose). |
| `RESTORE HEADERONLY / FILELISTONLY` | Backup-Metadaten vor der Wiederherstellung prüfen. |
| `sys.dm_io_virtual_file_stats` | I/O-Kennzahlen während der Fehleranalyse betrachten. |

## 🧩 Strategie für DBAs

PAGE RESTORE ist ein Notfallwerkzeug, kein Ersatz für vollständige Backups. Nimm es als **gezielten Eingriff** in deinen Disaster-Recovery-Plan auf, beispielsweise:
- wenn in einer großen Datenbank (über 1 TB) nur wenige Seiten beschädigt sind,
- wenn ein vollständiger Restore zu viel Ausfallzeit verursachen würde,
- oder wenn replizierte Daten eine möglichst kurze Wiederherstellungszeit besonders wichtig machen.

> „Die Kunst der Reparatur liegt darin zu verstehen, welche Teile unberührt bleiben sollten.“
> — *inspiriert von William James*

📚 **Repository:**
[SQLManiak/docs/PageRestore](https://github.com/marcinpytlik/SQLManiak/tree/master/docs/PageRestore.sql)

### 🧩 Checkliste

- [ ] Wiederherstellungsmodell FULL / BULK_LOGGED.
- [ ] `file_id:page_id` ermittelt.
- [ ] Full Backup und erforderliche Log-Backups verfügbar.
- [ ] Backup mit `RESTORE VERIFYONLY` geprüft.
- [ ] `RESTORE DATABASE … PAGE = 'X:Y' WITH NORECOVERY`.
- [ ] Erforderliche `RESTORE LOG`-Schritte mit anschließender Recovery.
- [ ] Validierung mit `DBCC CHECKDB` und `suspect_pages`.

*PAGE Restore ist Chirurgie, keine Transplantation. Du reparierst, was Aufmerksamkeit braucht, statt alles zu ersetzen.*
