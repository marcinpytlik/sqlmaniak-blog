---
title: "DELETE vs. TRUNCATE: Wann räumt SQL Server wirklich auf?"
date: 2025-10-15
slug: delete-vs-truncate
tags: [SQLServer, TSQL, Performance, Internals, DBA]
draft: false
---

Beide Befehle entfernen Daten. Doch der eine arbeitet mit chirurgischer Präzision, der andere mit dem Besen. `DELETE` und `TRUNCATE` sehen ähnlich aus — am Ende kann die Tabelle leer sein. Intern führt SQL Server jedoch völlig unterschiedliche Operationen aus.

### DELETE — der Chirurg mit der Lupe

`DELETE` arbeitet **Zeile für Zeile**. Jede gelöschte Zeile wird im Transaktionsprotokoll erfasst, sodass die Operation mit `ROLLBACK` zurückgesetzt werden kann.

Das bietet Präzision: `WHERE` ist möglich, DELETE-Trigger werden ausgelöst und Fremdschlüsselbeziehungen werden berücksichtigt. Der Preis: **Das Transaktionsprotokoll wächst**, und das Löschen vieler Zeilen kann aufwendig sein.

Das ist wie Aufräumen nach einer Party mit einer Pinzette — gründlich, aber langsam.

### TRUNCATE — der Bulldozer

`TRUNCATE TABLE` verarbeitet einzelne Zeilen nicht auf dieselbe Weise. SQL Server **gibt Datenseiten frei** (jeweils 8 KB) und protokolliert die Änderungen an den Zuordnungen statt jeder einzelnen gelöschten Zeile.

Deshalb ist der Befehl normalerweise schnell und benötigt **deutlich weniger Transaktionsprotokoll**.

Eine `WHERE`-Klausel ist nicht möglich; DELETE-Trigger werden nicht ausgelöst; und der `IDENTITY`-Zähler wird auf den Ausgangswert zurückgesetzt. Außerdem benötigt `TRUNCATE` die Berechtigung `ALTER` für die Tabelle und ist eingeschränkt, wenn ein Fremdschlüssel auf sie verweist.

Das ist wie das Ablassen eines ganzen Schwimmbeckens — schnell, aber ein einzelner Fisch lässt sich nicht zurücklassen.

### Transaktionsprotokoll, Backups und Spuren der Bereinigung

Auch `TRUNCATE` **kommt nicht ohne Transaktionsprotokollierung aus**. Die Freigabe von Seiten wird protokolliert und lässt sich beispielsweise mit `fn_dblog()` untersuchen.

SQL Server hinterlässt immer eine Spur — kleiner, aber ausreichend für die transaktionale Wiederherstellung.

Für Backups kann der Unterschied erheblich sein:
- `DELETE` kann viele Protokolleinträge erzeugen und nachfolgende Log-Backups vergrößern.
- `TRUNCATE` protokolliert in der Regel deutlich weniger und eignet sich daher zum Leeren von Staging- oder temporären Tabellen.

> „SQL Server merkt sich mehr, als man denkt. Selbst nach TRUNCATE bleibt eine Spur im Transaktionsprotokoll.“

### Bonus für Neugierige

So kannst du es ausprobieren:

```sql
CREATE TABLE Demo (ID INT IDENTITY, Data CHAR(100));
INSERT INTO Demo (Data) VALUES (REPLICATE('X', 100));
DELETE FROM Demo;
TRUNCATE TABLE Demo;
```

Sieh dir danach das Protokoll an:

```sql
SELECT [Operation], [Context], [Page ID]
FROM fn_dblog(NULL, NULL)
WHERE [AllocUnitName] LIKE '%Demo%';
```

Bei größeren Datenmengen lässt sich beobachten, dass `DELETE` wesentlich mehr zeilenbezogene Protokolleinträge erzeugt als `TRUNCATE`.

---

In der nächsten Folge unserer SQL-Internals-Reihe schauen wir uns **Ghost Records** an — denn selbst wenn Zeilen verschwunden scheinen, tut SQL Server manchmal nur so, als wären sie weg.
