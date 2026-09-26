---
title: "12 rzeczy, które DBA powinien sprawdzić przed wejściem w 2027 rok"
date: 2026-12-29T20:00:00+01:00
slug: sql-server-dba-year-end-checklist
description: "Końcoworoczna checklista SQL Server DBA: backup, restore, CHECKDB, joby, pojemność, Query Store, security, HA i dokumentacja."
tags: [SQLServer, DBA, Checklist, Monitoring, Maintenance]
categories: [SQL Server]
draft: false
---

Koniec roku to dobry moment, żeby sprawdzić nie tylko czy SQL Server działa.

Warto sprawdzić, czy jesteśmy przygotowani na moment, w którym przestanie działać.

## 1. Ostatnie backupy

```sql
SELECT
    database_name,
    type,
    MAX(backup_finish_date) AS LastBackup
FROM msdb.dbo.backupset
GROUP BY database_name, type
ORDER BY database_name, type;
```

## 2. Test restore

Zielony job backupowy nie jest testem odtworzenia. Sprawdź rzeczywisty restore i zmierz czas.

## 3. DBCC CHECKDB

Zweryfikuj, czy CHECKDB jest wykonywany dla wszystkich istotnych baz i czy wynik jest monitorowany.

## 4. Failed jobs

Nie patrz tylko na ostatni dzień. Szukaj wzorców i powtarzających się błędów.

## 5. Disabled jobs

Sprawdź, czy każdy wyłączony job jest wyłączony świadomie.

## 6. Wolne miejsce

Sprawdź wolne miejsce na woluminach, wielkość plików danych, logów i TempDB oraz trendy wzrostu.

## 7. Autogrowth

Autogrowth powinien być zabezpieczeniem, a nie codziennym mechanizmem zarządzania pojemnością.

## 8. Query Store

Sprawdź stan, rozmiar, read-only reason, wymuszone plany i znane regresje.

## 9. Security

Przejrzyj członków `sysadmin`, nieużywane loginy, konta usług i role w krytycznych bazach.

## 10. HA/DR

Sprawdź stan AG, FCI lub log shipping, monitoring oraz aktualność runbooka.

## 11. SQL Server Error Log i alerty

Sprawdź, czy nie powtarzają się błędy uznane wcześniej za chwilowe i czy alerty docierają do właściwych osób.

## 12. Dokumentacja

Zweryfikuj procedurę restore, kontakty, zależności, konta usług, punkty wejścia aplikacji i plan failover.

## Podsumowanie

Nie chodzi o 12 zielonych znaczników.

Chodzi o świadome potwierdzenie, że system jest monitorowany, odtwarzalny i zrozumiały.

Spokojny DBA kończy rok z wiedzą, a nie z nadzieją.