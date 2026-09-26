---
title: "Nie dawaj sysadmina — praktyczne podejście do uprawnień SQL Server"
date: 2026-12-08T20:00:00+01:00
slug: nie-dawaj-sysadmina
description: "Jak ograniczać uprawnienia w SQL Server zgodnie z zasadą najmniejszych uprawnień i dlaczego sysadmin nie powinien być domyślnym rozwiązaniem."
tags: [SQLServer, Security, Permissions, Sysadmin, DBA]
categories: [SQL Server]
draft: false
---

„Dodajmy mu sysadmina, żeby działało.”

To jedno z najdroższych zdań w administracji SQL Server.

## Kto ma sysadmin?

```sql
SELECT
    sp.name,
    sp.type_desc
FROM sys.server_role_members AS srm
JOIN sys.server_principals AS sr
    ON sr.principal_id = srm.role_principal_id
JOIN sys.server_principals AS sp
    ON sp.principal_id = srm.member_principal_id
WHERE sr.name = N'sysadmin'
ORDER BY sp.name;
```

Każdy wpis na tej liście powinien mieć uzasadnienie.

## Zacznij od potrzeby

Zamiast pytać „jaką rolę mam nadać?”, zapytaj: „jaką operację użytkownik lub aplikacja ma wykonać?”.

## Uprawnienia do procedur

```sql
GRANT EXECUTE ON OBJECT::dbo.usp_ProcessOrder
TO [AppUser];
```

## Odczyt jednej tabeli

```sql
GRANT SELECT ON OBJECT::dbo.Customers
TO [ReportingUser];
```

Nie zawsze potrzebujesz `db_datareader` dla całej bazy.

## Role własne

```sql
CREATE ROLE [reporting_reader];
GO
GRANT SELECT ON SCHEMA::reporting TO [reporting_reader];
GO
ALTER ROLE [reporting_reader] ADD MEMBER [DOMAIN\User];
```

## Podsumowanie

`sysadmin` nie powinien być skrótem do rozwiązywania problemów z uprawnieniami.

Spokojny DBA nadaje dokładnie tyle praw, ile potrzeba — i potrafi wyjaśnić dlaczego.