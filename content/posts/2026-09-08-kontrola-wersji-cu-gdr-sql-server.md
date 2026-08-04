---
title: "Jak kontrolować wersje, CU i GDR na wielu instancjach SQL Server?"
date: 2026-09-08
slug: kontrola-wersji-cu-gdr-sql-server
description: "Praktyczne podejście do inwentaryzacji buildów SQL Server, rozróżniania CU i GDR oraz planowania patchowania wielu instancji."
tags: [SQLServer, CU, GDR, Patching, DBA, Security]
categories: [SQL Server]
draft: false
---

Patchowanie jednej instancji SQL Server jest zadaniem technicznym.

Patchowanie kilkudziesięciu instancji staje się procesem zarządczym.

## Odczyt wersji instancji

```sql
SELECT
    @@SERVERNAME AS ServerName,
    SERVERPROPERTY('ProductVersion') AS ProductVersion,
    SERVERPROPERTY('ProductLevel') AS ProductLevel,
    SERVERPROPERTY('Edition') AS Edition,
    SERVERPROPERTY('ProductUpdateLevel') AS ProductUpdateLevel,
    SERVERPROPERTY('ProductUpdateReference') AS ProductUpdateReference;
```

Najważniejszy jest pełny numer buildu. Samo określenie „SQL Server 2022” nie wystarcza.

## CU i GDR

CU zawiera zbiorczy zestaw poprawek. GDR jest związany głównie z poprawkami bezpieczeństwa i krytycznymi poprawkami dla określonej gałęzi.

Najważniejsza zasada:

> Porównuj pełny numer buildu z zatwierdzonym baseline organizacji.

## Tabela baseline

```sql
CREATE SCHEMA patch;
GO

CREATE TABLE patch.SqlBuildBaseline
(
    SqlBuildBaselineId int IDENTITY(1,1) NOT NULL,
    MajorVersion int NOT NULL,
    ProductVersion varchar(50) NOT NULL,
    UpdateType varchar(20) NOT NULL,
    UpdateName varchar(100) NULL,
    ReleaseDate date NULL,
    IsApproved bit NOT NULL,
    IsCurrentTarget bit NOT NULL,
    Notes nvarchar(1000) NULL,
    CONSTRAINT PK_SqlBuildBaseline
        PRIMARY KEY CLUSTERED (SqlBuildBaselineId),
    CONSTRAINT UQ_SqlBuildBaseline_ProductVersion
        UNIQUE (ProductVersion)
);
GO
```

## Historia patchowania

Przechowuj:

- build przed aktualizacją,
- build po aktualizacji,
- czas rozpoczęcia i zakończenia,
- status,
- numer zmiany,
- wynik walidacji,
- informację o restarcie.

## Walidacja po patchingu

Sprawdź:

- wersję silnika,
- stan usług,
- SQL Server Error Log,
- stan baz,
- Always On lub FCI,
- SQL Server Agent,
- joby krytyczne,
- Database Mail,
- backup,
- monitoring.

```sql
SELECT
    name,
    state_desc,
    user_access_desc,
    recovery_model_desc
FROM sys.databases
ORDER BY name;
```

## Pełny proces

1. Inwentaryzacja.
2. Wybór buildu docelowego.
3. Analiza wymagań.
4. Test laboratoryjny.
5. Plan wycofania.
6. Okno serwisowe.
7. Instalacja.
8. Restart.
9. Walidacja.
10. Aktualizacja dokumentacji.

## Podsumowanie

Kontrola CU i GDR wymaga centralnego rejestru, baseline, historii i walidacji.

Spokojny DBA nie patchuje „na pamięć”.

Patchuje flotę na podstawie danych, standardu i udokumentowanego procesu.
