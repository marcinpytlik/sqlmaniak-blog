---
title: "Migracja SQL Server 2016 do 2022 — czego nie mówi kreator aktualizacji?"
date: 2026-10-06T20:00:00+02:00
slug: migracja-sql-server-2016-do-2022-ryzyka
description: "Najważniejsze obszary migracji SQL Server 2016 do 2022: compatibility level, plany wykonania, loginy, joby, SSIS, HA/DR i testy powdrożeniowe."
tags: [SQLServer, Migration, SQLServer2022, DBA, Upgrade]
categories: [SQL Server]
draft: false
---

Kreator instalacji potrafi sprawdzić wiele technicznych warunków.

Nie zna jednak procesów biznesowych, zależności aplikacji ani zachowania najważniejszych zapytań.

## Dwa poziomy migracji

Trzeba rozdzielić:

1. przeniesienie bazy na nowszy silnik,
2. przejście na wyższy Compatibility Level.

## Co trzeba przenieść poza bazą użytkownika?

- loginy i SID-y,
- role i uprawnienia serwerowe,
- Credential i Proxy,
- joby,
- operatory i alerty,
- linked servers,
- Database Mail,
- certyfikaty,
- klucze,
- SSISDB,
- ustawienia instancji.

## Użytkownicy osieroceni

```sql
SELECT
    dp.name AS DatabaseUser,
    dp.type_desc
FROM sys.database_principals AS dp
LEFT JOIN sys.server_principals AS sp
    ON dp.sid = sp.sid
WHERE dp.authentication_type_desc = 'INSTANCE'
  AND sp.sid IS NULL
  AND dp.name NOT IN
  (
      N'guest',
      N'dbo',
      N'sys',
      N'INFORMATION_SCHEMA'
  );
```

## Compatibility Level

```sql
SELECT
    name,
    compatibility_level
FROM sys.databases
ORDER BY name;
```

Zmiana:

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

powinna być osobnym etapem z Query Store i monitoringiem regresji.

## Obszary ryzyka wydajnościowego

- parameter sniffing,
- cardinality estimation,
- scalar UDF inlining,
- table variables,
- MSTVF,
- batch mode on rowstore,
- memory grants,
- stare hinty.

## Test powdrożeniowy

Sprawdź:

- stan baz,
- `DBCC CHECKDB`,
- loginy,
- joby,
- backup,
- monitoring,
- aplikację,
- integracje,
- wydajność,
- HA/DR,
- alerty,
- SQL Server Error Log.

## Plan wycofania

Rollback może obejmować:

- powrót aplikacji na starą instancję,
- tail-log backup,
- zmianę aliasu lub DNS,
- odtworzenie bazy,
- cofnięcie zmian integracyjnych.

## Podsumowanie

Migracja nie kończy się, gdy baza ma status `ONLINE`.

Spokojny DBA ocenia ją po tym, czy cały system działa poprawnie, jest monitorowany i można go bezpiecznie odtworzyć.
