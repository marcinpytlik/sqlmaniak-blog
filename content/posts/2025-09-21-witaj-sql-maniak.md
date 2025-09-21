
---
title: "Witaj, SQL Maniak!"
date: 2025-09-21
draft: false
description: "Start bloga technicznego o SQL Server, monitoringu i DevOps."
tags: ["SQL Server", "Monitoring", "Grafana", "InfluxDB", "PowerShell"]
categories: ["Start"]
---

Pierwszy wpis — hello, world!

- Repozytoria z kodem i skryptami będą linkowane tutaj.
- Na LinkedIn publikuję zajawki i dyskusje — pełne wersje lądują na blogu.

### Przykład kodu T-SQL

```sql
SELECT
    s.session_id,
    r.status,
    r.cpu_time,
    r.total_elapsed_time,
    t.text AS sql_text
FROM sys.dm_exec_requests AS r
JOIN sys.dm_exec_sessions AS s ON s.session_id = r.session_id
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) AS t
WHERE s.is_user_process = 1
ORDER BY r.total_elapsed_time DESC;
```

### PowerShell

```powershell
Get-Service *SQL* | Sort-Object Status, DisplayName | Format-Table -Auto
```

Miłej lektury i do zobaczenia w następnym wpisie! 🚀
