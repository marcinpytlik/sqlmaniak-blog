---
title: "Ghost Records: Geister in der Datenbank"
date: 2025-10-16
slug: ghost-records
tags: [SQLServer, Internals, DBCC, GhostCleanup, DBA]
draft: false
---

In der Datenbank spukt es. Nicht im Horrorfilm, sondern in der DMV `sys.dm_db_index_physical_stats`. Wenn du eine Zeile löschst, entfernt SQL Server sie nicht unbedingt sofort. Stattdessen bleibt ein **Ghost Record** zurück, bis der *Ghost Cleanup Task* den Geist vertreibt.

Dieses Verfahren unterstützt den transaktionalen Rollback und vermeidet unnötige Störungen bei `DELETE`. Die Engine markiert einen Datensatz lieber als gelöscht, statt die Datenseite sofort umzustrukturieren.

> „Nur weil du etwas nicht siehst, heißt das nicht, dass es nicht existiert — besonders in einer Datenbank.“

---

### Wie ein Geist entsteht

Wenn du `DELETE` ausführst, geschieht Folgendes:
1. SQL Server markiert den Datensatz über Metadaten im Datensatzheader als *ghosted*.
2. Der gelöschte Datensatz ist für gewöhnliche Abfragen nicht mehr sichtbar.
3. Die Bytes bleiben auf der Datenseite, bis sie sicher entfernt werden können.

Das ist kein Fehler, sondern ein **Mechanismus für Performance und Wiederherstellung**. Er unterstützt das Zurückrollen von Änderungen und die Koordination paralleler Vorgänge, ohne jeden gelöschten Datensatz sofort physisch zu entfernen.

---

### Die Geisteraustreibung: Ghost Cleanup Task

Der *Ghost Cleanup Task* sucht regelmäßig im Hintergrund nach geeigneten Ghost Records und entfernt sie physisch. Das kann nicht immer sofort geschehen. SQL Server muss berücksichtigen:
- aktive Transaktionen, die den Datensatz noch benötigen könnten,
- Zeilenversionen, die parallele Leser benötigen,
- Sperren und andere Bedingungen, die die Bereinigung verzögern.

Nach umfangreichen Löschvorgängen, bei lang laufenden Transaktionen oder mit aktiviertem **READ_COMMITTED_SNAPSHOT** können Ghost Records deshalb länger bestehen bleiben, während Leser Versionen in tempdb benötigen.

---

### So findest du sie

Mit `SELECT *` sind Geister nicht sichtbar, aber Diagnosewerkzeuge können sie aufspüren:

```sql
DBCC CHECKTABLE ('TwojaTabela') WITH TABLERESULTS;
```

Die Ausgabe kann einen Wert `GhostRecCnt` enthalten, der auf noch zu bereinigende Datensätze hinweist. Weitere Informationen liefert die DMV:

```sql
SELECT
    object_name(object_id) AS [Tabela],
    index_type_desc,
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED')
WHERE ghost_record_count > 0;
```

---

### Wenn die Geister nicht verschwinden

Manchmal kommt der *Ghost Cleanup Task* nicht hinterher, etwa nach vielen `DELETE`-Operationen. In kontrollierten Umgebungen wird gelegentlich folgender Diagnosebefehl verwendet:

```sql
DBCC FORCEGHOSTCLEANUP;
```

Damit wird die Bereinigung ausdrücklich angestoßen. Vorsicht: Sie kann I/O verursachen. Berücksichtige daher die Auswirkungen und verwende den Befehl nicht unbedacht in der Produktion.

---

### Warum ist das wichtig?

Ghost Records gehören zur Wiederherstellungs- und Nebenläufigkeitsarchitektur von SQL Server, die auf **Write-Ahead Logging** und transaktionaler Konsistenz beruht. Ein logisches Löschen bedeutet nicht immer die sofortige physische Entfernung.

Das Löschen von Daten ist ein Prozess, kein einzelner Augenblick. Jedes `DELETE` ist das Versprechen, dass die Engine später aufräumt, sobald es sicher ist.

---

> „Manchmal lebt das Tote weiter — bis das Transaktionsprotokoll festhält, dass es wirklich verschwunden ist.“

---

### Experiment

Probiere es selbst:

```sql
CREATE TABLE GhostDemo(Id INT IDENTITY PRIMARY KEY, Data CHAR(200) DEFAULT 'x');
GO
INSERT INTO GhostDemo DEFAULT VALUES;
GO 1000
DELETE FROM GhostDemo WHERE Id <= 900;
GO
DBCC CHECKTABLE('GhostDemo') WITH TABLERESULTS;
```

Prüfe `GhostRecCnt` und beobachte, wie lange gelöschte Datensätze bestehen bleiben. Warte etwas und wiederhole die Prüfung, um zu sehen, ob die Bereinigung inzwischen erfolgt ist.

---

Ein Blick auf Ghost Records zeigt den **Zwischenzustand der Daten** — den Bereich zwischen „war vorhanden“ und „ist verschwunden“. SQL Server kennt diese Grenzen und hält die Datenwelt geordnet, selbst wenn es manchmal darin spukt.
