---
title: "Dlaczego job SQL Server Agent zakończył się błędem? Diagnostyka krok po kroku"
date: 2026-08-25
slug: diagnostyka-bledow-sql-server-agent-krok-po-kroku
description: "Metodyczna diagnostyka błędów jobów SQL Server Agent: historia, pierwszy błędny krok, konto wykonawcze, proxy, harmonogram i logi."
tags: [SQLServer, SQLServerAgent, Troubleshooting, Jobs, DBA]
categories: [SQL Server]
draft: false
---

Komunikat „The job failed” nie jest diagnozą.

Prawdziwa diagnostyka zaczyna się od ustalenia, który krok zawiódł jako pierwszy, w jakim kontekście bezpieczeństwa działał i co zmieniło się od ostatniego poprawnego wykonania.

## Krok 1. Ustal pierwszy błędny krok

```sql
SELECT TOP (100)
    j.name AS JobName,
    msdb.dbo.agent_datetime(h.run_date, h.run_time) AS RunDateTime,
    h.step_id,
    h.step_name,
    h.run_status,
    h.sql_severity,
    h.sql_message_id,
    h.message
FROM msdb.dbo.sysjobhistory AS h
INNER JOIN msdb.dbo.sysjobs AS j
    ON h.job_id = j.job_id
WHERE j.name = N'TwojJob'
ORDER BY h.instance_id DESC;
```

## Krok 2. Sprawdź konfigurację kroku

```sql
SELECT
    j.name AS JobName,
    s.step_id,
    s.step_name,
    s.subsystem,
    s.database_name,
    s.command,
    s.retry_attempts,
    s.retry_interval,
    s.on_success_action,
    s.on_fail_action,
    s.proxy_id,
    s.output_file_name
FROM msdb.dbo.sysjobsteps AS s
INNER JOIN msdb.dbo.sysjobs AS j
    ON s.job_id = j.job_id
WHERE j.name = N'TwojJob'
ORDER BY s.step_id;
```

## Krok 3. Ustal kontekst bezpieczeństwa

```sql
SELECT
    j.name AS JobName,
    SUSER_SNAME(j.owner_sid) AS JobOwner,
    s.step_id,
    s.step_name,
    s.subsystem,
    p.name AS ProxyName,
    c.name AS CredentialName,
    c.credential_identity
FROM msdb.dbo.sysjobs AS j
INNER JOIN msdb.dbo.sysjobsteps AS s
    ON j.job_id = s.job_id
LEFT JOIN msdb.dbo.sysproxies AS p
    ON s.proxy_id = p.proxy_id
LEFT JOIN sys.credentials AS c
    ON p.credential_id = c.credential_id
WHERE j.name = N'TwojJob';
```

Popularny przypadek brzmi:

> Skrypt działa ręcznie, ale nie działa jako job.

Najczęściej oznacza to różnicę w koncie, profilu PowerShell, ścieżkach, zmiennych środowiskowych albo dostępie do udziału sieciowego.

## Krok 4. Sprawdź właściciela i harmonogram

```sql
SELECT
    name AS JobName,
    SUSER_SNAME(owner_sid) AS JobOwner
FROM msdb.dbo.sysjobs
WHERE name = N'TwojJob';
```

Właścicielem joba nie powinno być przypadkowe konto pracownika.

## Krok 5. Sprawdź logi właściwego subsystemu

Dla T-SQL analizuj historię joba, SQL Server Error Log i Extended Events.

Dla PowerShell zapisuj pełny wyjątek, kod wyjścia i plik logu.

Dla SSIS korzystaj z raportów SSISDB.

Dla CmdExec sprawdzaj stdout, stderr, kod zakończenia oraz konto wykonawcze.

## Krok 6. Porównaj z ostatnim sukcesem

Sprawdź:

- wdrożenia,
- zmianę hasła,
- patching,
- failover,
- zmianę DNS,
- zmianę ścieżki,
- brak miejsca,
- zmianę uprawnień,
- zmianę parametrów.

## Podsumowanie

Błąd joba należy analizować warstwowo: wykonanie, krok, subsystem, bezpieczeństwo, harmonogram i zależności.

Spokojny DBA nie zatrzymuje się na komunikacie „job failed”.

Dociera do pierwszej technicznej przyczyny i zamienia incydent w poprawę procesu.
