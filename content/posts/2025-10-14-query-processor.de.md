---
title: "Was sieht der Query Processor, bevor du auf Execute klickst?"
date: 2025-10-14
slug: query-processor
tags: [SQLServer, TSQL, DBA, SQLQuiz, DataPlatform]
draft: false
---

Wenn du ein `SELECT` eingibst und auf **Execute** klickst, beginnt etwas Erstaunliches — allerdings nicht in der Reihenfolge, die du vielleicht erwartest.

SQL Server ist kein naiver Interpreter deines Codes. Er ist ein **Compiler für Abfragelogik**, der die Welt anders betrachtet. Bevor die Abfrage ausgeführt wird, wird der T-SQL-Text **analysiert, umgeschrieben, normalisiert und optimiert**. Das Ergebnis ist nicht einfach „Code ausführen“, sondern ein **Abfrageplan**: eine präzise Anleitung für die relationale Engine, Daten möglichst effizient abzurufen.

Hier zeigt sich das erste Paradox: SQL Server beginnt logisch nicht mit `SELECT`. Zunächst werden über `FROM` die Datenquellen und Verknüpfungen bestimmt. Danach folgen die logischen Verarbeitungsschritte:

1. `FROM` + `JOIN` — Datenquellen und Verknüpfungen bestimmen.
2. `WHERE` — Zeilen filtern.
3. `GROUP BY` und Aggregatfunktionen — Zusammenfassungen erstellen.
4. `HAVING` — Gruppen filtern.
5. `SELECT` — Ausgabespalten und Ausdrücke auswählen.
6. `ORDER BY` — das Ergebnis sortieren.

Es ist kein Zufall, dass die Performance häufig davon abhängt, **wo** gefiltert wird, und nicht davon, **wie** schön der SQL-Code aussieht.

> „Die Illusion, dass Code genau so ausgeführt wird, wie er geschrieben wurde, gehört zu den ältesten Tricks der Informatik.“

Diese Illusion gilt auch für SQL. Die Syntax wirkt sequenziell, doch der Query Processor denkt in relationaler Algebra. Deshalb kann das Umschreiben eines Filters oder Joins einen Ausführungsplan erheblich verändern. Wer diese Logik versteht, schreibt Abfragen **nicht nur korrekt, sondern effizient**.

---

### So überprüfst du es in der Praxis

Probiere es selbst aus. Führe die folgende Abfrage in SSMS oder Azure Data Studio aus:

```sql
USE AdventureWorks2022;
SET SHOWPLAN_XML ON;

SELECT p.Name, SUM(sod.LineTotal) AS Total
FROM Sales.SalesOrderDetail sod
JOIN Production.Product p ON sod.ProductID = p.ProductID
WHERE p.Color = 'Red'
GROUP BY p.Name
HAVING SUM(sod.LineTotal) > 10000
ORDER BY Total DESC;
```

SQL Server **führt die Abfrage nicht aus**, sondern erzeugt einen XML-Ausführungsplan. Öffne ihn und achte auf den Datenzugriff: **SCAN oder SEEK**, etwa `Clustered Index Scan` oder `Index Seek`. Weitere Operatoren können `Nested Loops`, `Hash Match` und `Filter` sein. Der Operatorbaum bildet den SQL-Text nicht Zeile für Zeile ab.

Deaktiviere die Planausgabe mit:

```sql
SET SHOWPLAN_XML OFF;
```

Du möchtest den Plan grafisch sehen? Aktiviere vor der Ausführung `Ctrl+M`. Im grafischen Plan von SSMS steht `SELECT` an der Wurzel des Operatorbaums; die Datenzugriffe liegen an dessen Blättern.

---

Siehst du? Das ist keine Magie, sondern **relationale Algebra in Aktion**. Jedes `SELECT` wird zu einer Komposition von Operatoren, die der Query Processor anordnet. Wenn du diesen Unterschied verstehst, hörst du auf, Abfragen nur zu schreiben — und beginnst, sie zu **entwerfen**.
