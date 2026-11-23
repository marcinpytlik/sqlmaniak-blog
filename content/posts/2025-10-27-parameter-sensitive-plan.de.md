---
title: "Parameter Sensitive Plan: Kontextbewusste Intelligenz in SQL Server"
date: 2025-10-27
slug: parameter-sensitive-plan
tags: [SQLServer, PSP, Performance, QueryOptimization, Internals]
draft: false
---

Jeder Ausführungsplan ist eine Entscheidung darüber, **wie aus Daten ein Ergebnis wird**. Über viele Jahre konnte SQL Server einen für den ersten Parameterwert optimierten Plan zwischenspeichern (Parameter Sniffing) und wiederverwenden, selbst wenn spätere Werte eine ganz andere Datenverteilung aufwiesen.

## 💡 Was bringt PSP in SQL Server 2022?

Die **Parameter Sensitive Plan (PSP)**-Optimierung kann **mehrere Planvarianten** für **dieselbe Abfrage** vorhalten, die für unterschiedliche Parameterselektivitäten optimiert sind. Ein **Dispatcher** wählt die passende Variante anhand der aktuellen Parameterwerte aus.

- Eine logische Abfrage kann mehrere Planvarianten besitzen.
- Query Store erfasst Informationen, mit denen sich diese Varianten analysieren lassen.
- Zur Laufzeit hängt die Auswahl von Selektivitätsbereichen („Buckets“) ab.

📂 Repository: [PSP](https://github.com/marcinpytlik/SQLManiak/tree/master/sqlmaniak_blog/PSP-DEMO)

## ⚙️ Demo starten

1. Öffne das Repository in VS Code.
2. Setze die Umgebungsvariablen:

   ```powershell
   $env:MSSQL_SERVER="localhost"
   $env:MSSQL_USER="sa"
   $env:MSSQL_PASS="YourStrong!Passw0rd"
   ```

3. Starte die Tasks **00 → 03**, danach **04 – Compare IO/CPU**, oder führe die Abfragen im Ordner `sql/dmv` aus.

## 🔬 Was du sehen wirst

- **Mindestens zwei Planvarianten** in Query Store für `dbo.GetOrdersByCustomer`.
- Im Plan-XML: `<ParameterSensitivePlan>True</ParameterSensitivePlan>`.
- Unterschiede bei I/O und CPU zwischen seltenen und „heißen“ Parameterwerten.

## 🧩 Bewährte Vorgehensweisen

- Halte **Query Store im Modus READ_WRITE**, um PSP zu analysieren.
- Sei vorsichtig, wenn du PSP mit `OPTIMIZE FOR`-Hints kombinierst.
- PSP gilt für geeignete parametrisierte Anweisungen, einschließlich Stored Procedures und `sp_executesql`.

> „Intelligenz ist die Fähigkeit, sich an Veränderungen anzupassen.“ — *Stephen Hawking*
