---
title: "Nie dawaj sysadmina. Zaprojektuj uprawnienia w SQL Server"
date: 2026-08-14T00:01:00+02:00
slug: "nie-dawaj-sysadmina-uprawnienia-sql-server"
description: "Jak zaprojektować uprawnienia w SQL Server zgodnie z zasadą least privilege zamiast nadawać rolę sysadmin przy każdym problemie z dostępem."
category: "Piątkowe różności"
tags:
  - SQL Server
  - bezpieczeństwo
  - sysadmin
  - least privilege
  - uprawnienia
  - SQL Server Agent
draft: false
---

# Nie dawaj sysadmina. Zaprojektuj uprawnienia w SQL Server

W SQL Server jest jedna rola, która potrafi rozwiązać niemal każdy problem z uprawnieniami.

`sysadmin`.

Użytkownik nie może utworzyć bazy?

Dodajmy `sysadmin`.

Job nie chce się uruchomić?

Dodajmy `sysadmin`.

Deployment się nie udaje?

Dodajmy `sysadmin`.

Technicznie problem często znika.

Tylko że razem z nim znika również duża część kontroli nad bezpieczeństwem.

`sysadmin` nie powinien być odpowiedzią na każdy komunikat `permission denied`.

Powinien być świadomą decyzją administracyjną.

> `sysadmin` nie jest rozwiązaniem problemu z uprawnieniami. Bardzo często jest po prostu rezygnacją z ich projektowania.

W tym artykule pokażę, jak podejść do tego inaczej: zacząć od rzeczywistych operacji, które konto musi wykonywać, a dopiero potem dobrać odpowiednie role i uprawnienia.

## Problem: konto techniczne potrzebuje „dużo uprawnień”

Załóżmy, że mamy konto deploymentowe.

Ma ono:

* tworzyć bazy danych,
* wykonywać podstawową diagnostykę instancji,
* tworzyć i uruchamiać joby SQL Server Agent,
* wykonywać określone zadania administracyjne,
* w przyszłości wykonywać deploymenty, na przykład do SSISDB,
* ale nie powinno być administratorem całej instancji.

Najprostsze rozwiązanie wygląda tak:

```sql
ALTER SERVER ROLE [sysadmin]
ADD MEMBER [SQLDeployDemo];
```

I wszystko zaczyna działać.

Problem polega na tym, że konto dostało znacznie więcej możliwości, niż rzeczywiście potrzebuje.

Może zarządzać całą instancją.

Może zmieniać konfigurację.

Może zarządzać loginami.

Może przejmować dostęp do baz danych.

Może wykonywać operacje administracyjne, których jego zadanie w ogóle nie dotyczy.

To nie jest już rozwiązanie problemu z uprawnieniami.

To jest ominięcie modelu bezpieczeństwa.

## Nie zaczynaj od roli

Najważniejsza zmiana sposobu myślenia jest bardzo prosta.

Nie zaczynaj od pytania:

> Jaką rolę mam nadać użytkownikowi?

Zacznij od pytania:

> Jakie dokładnie operacje ten użytkownik ma wykonywać?

Dopiero później mapuj je na:

* uprawnienia serwerowe,
* role serwerowe,
* role bazodanowe,
* role w `msdb`,
* SQL Server Agent Proxy,
* uprawnienia w SSISDB,
* własne role serwerowe.

To jest istota zasady **least privilege**.

Konto powinno mieć dokładnie tyle praw, ile potrzebuje do wykonania swojej pracy.

Ani mniej.

Ani więcej.

## Demo bez domeny

Do pokazania mechanizmu nie potrzebujemy Active Directory.

Wystarczy zwykły login SQL Server.

```sql
USE [master];
GO

CREATE LOGIN [SQLDeployDemo]
WITH

    PASSWORD = N'SQL-Demo-Only!2026',
    CHECK_POLICY = OFF,
    CHECK_EXPIRATION = OFF
;
GO
```

Sprawdźmy, czy konto jest członkiem `sysadmin`.

```sql
SELECT
    IS_SRVROLEMEMBER
    (
        N'sysadmin',
        N'SQLDeployDemo'
    ) AS IsSysadmin;
GO
```

Oczekiwany wynik:

```text
0
```

I właśnie taki stan chcemy zachować.

## Konto ma tworzyć bazy danych

Jeżeli konto ma tworzyć bazy, nie oznacza to automatycznie, że potrzebuje `sysadmin`.

Możemy wykorzystać rolę:

```sql
ALTER SERVER ROLE [dbcreator]
ADD MEMBER [SQLDeployDemo];
GO
```

Teraz konto może tworzyć bazy danych, ale nadal nie kontroluje całej instancji.

## Własna rola serwerowa

Załóżmy, że konto potrzebuje również podstawowego dostępu diagnostycznego.

Możemy stworzyć własną rolę serwerową:

```sql
CREATE SERVER ROLE [DeployOperators];
GO
```

Następnie nadać jej konkretne uprawnienia:

```sql
GRANT VIEW SERVER STATE
TO [DeployOperators];
GO

GRANT VIEW ANY DATABASE
TO [DeployOperators];
GO
```

I dodać konto do tej roli:

```sql
ALTER SERVER ROLE [DeployOperators]
ADD MEMBER [SQLDeployDemo];
GO
```

Możemy teraz sprawdzić członkostwo:

```sql
SELECT
    MemberPrincipal.name AS MemberName,
    RolePrincipal.name AS ServerRole
FROM sys.server_role_members AS RoleMember
INNER JOIN sys.server_principals AS RolePrincipal
    ON RolePrincipal.principal_id =
       RoleMember.role_principal_id
INNER JOIN sys.server_principals AS MemberPrincipal
    ON MemberPrincipal.principal_id =
       RoleMember.member_principal_id
WHERE MemberPrincipal.name = N'SQLDeployDemo'
ORDER BY RolePrincipal.name;
GO
```

Powinniśmy zobaczyć:

```text
dbcreator
DeployOperators
```

Nie zobaczymy:

```text
sysadmin
```

I właśnie o to chodzi.

## Test pozytywny: użytkownik może zrobić to, czego potrzebuje

Przełączmy kontekst bezpieczeństwa.

```sql
EXECUTE AS LOGIN = N'SQLDeployDemo';
GO
```

Sprawdźmy, jako kto aktualnie działamy:

```sql
SELECT
    ORIGINAL_LOGIN() AS OriginalLogin,
    SUSER_SNAME() AS CurrentLogin;
GO
```

Teraz wykonajmy operację, którą konto rzeczywiście ma wykonywać:

```sql
CREATE DATABASE [DemoDeploymentDatabase];
GO
```

Jeżeli wszystko zostało skonfigurowane poprawnie, baza zostanie utworzona.

Wracamy do poprzedniego kontekstu:

```sql
REVERT;
GO
```

To jest pierwszy test modelu bezpieczeństwa.

**Operacja dozwolona powinna się udać.**

## Test negatywny: użytkownik nie może przekroczyć granicy

To jednak dopiero połowa testu.

Dobry model uprawnień powinien również potwierdzać, że użytkownik **nie może zrobić czegoś, czego robić nie powinien**.

Ponownie przełączamy kontekst:

```sql
EXECUTE AS LOGIN = N'SQLDeployDemo';
GO
```

Spróbujmy dodać konto do `sysadmin`:

```sql
BEGIN TRY

    ALTER SERVER ROLE [sysadmin]
    ADD MEMBER [SQLDeployDemo];

END TRY
BEGIN CATCH

    PRINT 'OCZEKIWANY BŁĄD:';
    PRINT ERROR_MESSAGE();

END CATCH;
GO
```

Wracamy:

```sql
REVERT;
GO
```

I ponownie sprawdzamy:

```sql
SELECT
    IS_SRVROLEMEMBER
    (
        N'sysadmin',
        N'SQLDeployDemo'
    ) AS IsSysadmin;
GO
```

Wynik nadal powinien wynosić:

```text
0
```

To jest dokładnie ten model, którego szukamy.

Konto może wykonać potrzebną operację.

Nie może przekroczyć granicy, którą dla niego zaprojektowaliśmy.

## Sprawdź efektywne uprawnienia

Przy projektowaniu bezpieczeństwa warto nie tylko analizować przypisane role, ale również sprawdzać efektywne uprawnienia.

SQL Server udostępnia do tego między innymi:

```sql
EXECUTE AS LOGIN = N'SQLDeployDemo';
GO

SELECT
    permission_name
FROM sys.fn_my_permissions
(
    NULL,
    N'SERVER'
)
ORDER BY permission_name;
GO

REVERT;
GO
```

To przydatny sposób na sprawdzenie, co konto rzeczywiście może zrobić po uwzględnieniu członkostwa w rolach oraz bezpośrednio nadanych uprawnień.

## SQL Server Agent również nie wymaga sysadmina

Kolejny często spotykany argument brzmi:

> Konto musi zarządzać jobami, więc potrzebuje sysadmin.

Nie musi.

SQL Server Agent posiada własny model bezpieczeństwa.

W bazie `msdb` dostępne są trzy podstawowe role:

```text
SQLAgentUserRole
SQLAgentReaderRole
SQLAgentOperatorRole
```

Każda daje inny poziom dostępu.

Na potrzeby demo tworzymy użytkownika:

```sql
USE [msdb];
GO

CREATE USER [SQLDeployDemo]
FOR LOGIN [SQLDeployDemo];
GO
```

Następnie dodajemy go do:

```sql
ALTER ROLE [SQLAgentOperatorRole]
ADD MEMBER [SQLDeployDemo];
GO
```

Możemy sprawdzić członkostwo:

```sql
SELECT
    DatabasePrincipal.name AS UserName,
    DatabaseRole.name AS RoleName
FROM sys.database_role_members AS RoleMember
INNER JOIN sys.database_principals AS DatabaseRole
    ON DatabaseRole.principal_id =
       RoleMember.role_principal_id
INNER JOIN sys.database_principals AS DatabasePrincipal
    ON DatabasePrincipal.principal_id =
       RoleMember.member_principal_id
WHERE DatabasePrincipal.name = N'SQLDeployDemo';
GO
```

To nadal nie robi z naszego użytkownika administratora całej instancji.

## Tworzenie joba bez sysadmina

Przełączmy kontekst na konto demo:

```sql
USE [msdb];
GO

EXECUTE AS LOGIN = N'SQLDeployDemo';
GO
```

Tworzymy prosty job:

```sql
EXEC dbo.sp_add_job
    @job_name = N'DEMO - Least Privilege',
    @enabled = 1,
    @description =
        N'Job utworzony przez użytkownika bez sysadmin.';
GO
```

Dodajemy krok:

```sql
EXEC dbo.sp_add_jobstep
    @job_name = N'DEMO - Least Privilege',
    @step_name = N'Test T-SQL',
    @subsystem = N'TSQL',
    @database_name = N'master',
    @command = N'
        SELECT
            @@SERVERNAME AS ServerName,
            SUSER_SNAME() AS LoginName,
            SYSDATETIME() AS ExecutionTime;
    ';
GO
```

Przypisujemy job do lokalnego serwera:

```sql
EXEC dbo.sp_add_jobserver
    @job_name = N'DEMO - Least Privilege';
GO
```

Wracamy do poprzedniego kontekstu:

```sql
REVERT;
GO
```

Teraz możemy sprawdzić właściciela joba:

```sql
SELECT
    j.name AS JobName,
    SUSER_SNAME(j.owner_sid) AS JobOwner,
    j.enabled,
    j.description
FROM msdb.dbo.sysjobs AS j
WHERE j.name = N'DEMO - Least Privilege';
GO
```

Mamy więc kolejny przykład operacji administracyjnej, którą można wykonać bez nadawania pełnej kontroli nad instancją.

## A co z PowerShell i CmdExec?

Tutaj pojawia się ważna granica.

Krok `TSQL` działa wewnątrz mechanizmów SQL Server.

Ale SQL Server Agent może uruchamiać również:

* PowerShell,
* CmdExec,
* SSIS,
* inne subsystemy.

Takie operacje mogą wychodzić poza sam silnik SQL Server.

I właśnie tutaj pojawiają się:

* **Credential**,
* **SQL Server Agent Proxy**.

Schemat wygląda mniej więcej tak:

```text
Login SQL
   |
   v
SQL Server Agent
   |
   v
Proxy
   |
   v
Credential
   |
   v
konto systemu operacyjnego
```

Zamiast:

```text
Login
   |
   v
sysadmin
   |
   v
wszystko
```

Proxy pozwala kontrolować, kto może uruchomić konkretny subsystem i pod jaką tożsamością systemową.

To znacznie lepszy model niż rozszerzanie praw użytkownika tylko po to, żeby job zaczął działać.

## SSISDB również ma własny model bezpieczeństwa

Podobna sytuacja występuje przy SSIS.

Jeżeli korzystamy z Integration Services Catalog, nie powinniśmy automatycznie zakładać:

> Deployment SSIS = sysadmin.

SSISDB posiada własny model uprawnień.

Możemy oddzielić:

* administratora katalogu,
* osobę wdrażającą projekty,
* operatora wykonującego pakiety,
* użytkowników mających dostęp tylko do wybranych folderów lub projektów.

Znowu wracamy do tej samej zasady.

Nie pytamy:

> Jaką największą rolę mogę nadać?

Pytamy:

> Jakiej konkretnie operacji potrzebuje to konto?

## Uważaj na securityadmin

W takich scenariuszach często pojawia się również rola:

```text
securityadmin
```

Trzeba jednak podchodzić do niej ostrożnie.

Jeżeli konto potrzebuje zarządzać bezpieczeństwem, nie oznacza to automatycznie, że powinno zarządzać całym bezpieczeństwem instancji.

Czasami lepszym rozwiązaniem będzie:

* własna server role,
* konkretne `GRANT`,
* role bazodanowe,
* procedury podpisane certyfikatem,
* separacja obowiązków.

Im silniejsza rola stała, tym dokładniej warto przeanalizować jej rzeczywiste możliwości.

## Testuj bezpieczeństwo w obie strony

To jedna z najważniejszych zasad całego procesu.

Bardzo często testujemy tylko:

> Czy użytkownik potrafi wykonać operację?

To za mało.

Powinniśmy testować dwa przypadki.

### Test pozytywny

Operacja dozwolona powinna działać.

Na przykład:

```sql
CREATE DATABASE [DemoDeploymentDatabase];
```

### Test negatywny

Operacja zabroniona powinna zakończyć się błędem.

Na przykład:

```sql
ALTER SERVER ROLE [sysadmin]
ADD MEMBER [SQLDeployDemo];
```

Dopiero gdy oba przypadki zachowują się zgodnie z oczekiwaniem, możemy powiedzieć, że granica bezpieczeństwa działa poprawnie.

## Jak projektować uprawnienia krok po kroku?

Można zastosować prosty schemat.

### 1. Zidentyfikuj operacje

Przykład:

```text
CREATE DATABASE
VIEW SERVER STATE
CREATE JOB
START JOB
DEPLOY SSIS PROJECT
```

### 2. Określ zakres

Czy operacja dotyczy:

* całej instancji,
* jednej bazy,
* `msdb`,
* SSISDB,
* systemu operacyjnego?

### 3. Dobierz mechanizm

Może to być:

* konkretne `GRANT`,
* fixed server role,
* custom server role,
* database role,
* SQL Server Agent role,
* Proxy,
* Credential,
* certyfikat.

### 4. Nadaj minimalny zestaw praw

Nie więcej niż potrzeba.

### 5. Wykonaj test pozytywny

Sprawdź, czy konto potrafi wykonać swoją pracę.

### 6. Wykonaj test negatywny

Sprawdź, czy nie może zrobić czegoś dodatkowego.

### 7. Udokumentuj model

Za pół roku powinno być wiadomo:

* dlaczego konto ma dane uprawnienie,
* do czego jest ono wykorzystywane,
* jakie operacje są dozwolone,
* jakie operacje powinny pozostać zabronione.

## Pełne demo

Poniższy skrypt zbiera podstawową konfigurację środowiska demonstracyjnego.

```sql
USE [master];
GO

CREATE LOGIN [SQLDeployDemo]
WITH

    PASSWORD = N'SQL-Demo-Only!2026',
    CHECK_POLICY = OFF,
    CHECK_EXPIRATION = OFF
;
GO

ALTER SERVER ROLE [dbcreator]
ADD MEMBER [SQLDeployDemo];
GO

CREATE SERVER ROLE [DeployOperators];
GO

GRANT VIEW SERVER STATE
TO [DeployOperators];
GO

GRANT VIEW ANY DATABASE
TO [DeployOperators];
GO

ALTER SERVER ROLE [DeployOperators]
ADD MEMBER [SQLDeployDemo];
GO

USE [msdb];
GO

CREATE USER [SQLDeployDemo]
FOR LOGIN [SQLDeployDemo];
GO

ALTER ROLE [SQLAgentOperatorRole]
ADD MEMBER [SQLDeployDemo];
GO
```

Test pozytywny:

```sql
USE [master];
GO

EXECUTE AS LOGIN = N'SQLDeployDemo';
GO

CREATE DATABASE [DemoDeploymentDatabase];
GO

REVERT;
GO
```

Test negatywny:

```sql
EXECUTE AS LOGIN = N'SQLDeployDemo';
GO

BEGIN TRY

    ALTER SERVER ROLE [sysadmin]
    ADD MEMBER [SQLDeployDemo];

END TRY
BEGIN CATCH

    PRINT 'OCZEKIWANY BŁĄD:';
    PRINT ERROR_MESSAGE();

END CATCH;
GO

REVERT;
GO
```

Na koniec sprawdzamy stan:

```sql
SELECT
    N'SQLDeployDemo' AS LoginName,
    IS_SRVROLEMEMBER
    (
        N'sysadmin',
        N'SQLDeployDemo'
    ) AS IsSysadmin,
    IS_SRVROLEMEMBER
    (
        N'dbcreator',
        N'SQLDeployDemo'
    ) AS IsDbCreator;
GO
```

Oczekiwany rezultat:

```text
LoginName       IsSysadmin   IsDbCreator
--------------- ------------ -----------
SQLDeployDemo   0            1
```

I właśnie ten wynik najlepiej podsumowuje całe podejście.

Konto ma uprawnienie, którego potrzebuje.

Nie ma pełnej kontroli nad instancją.

## Podsumowanie

`sysadmin` jest wygodny.

Jeżeli konto nie może czegoś zrobić, jedno polecenie potrafi usunąć problem:

```sql
ALTER SERVER ROLE [sysadmin]
ADD MEMBER [...];
```

Tylko że zadaniem administratora nie powinno być wyłącznie doprowadzenie do sytuacji:

> działa.

Powinniśmy również wiedzieć:

> dlaczego działa i co jeszcze użytkownik może zrobić.

Dlatego zamiast traktować `sysadmin` jak lekarstwo na każdy `permission denied`, warto rozłożyć wymagania na konkretne operacje.

Tworzenie baz?

Nadaj odpowiednie uprawnienia do tworzenia baz.

Diagnostyka?

Nadaj konkretne uprawnienia diagnostyczne.

SQL Server Agent?

Skorzystaj z modelu bezpieczeństwa `msdb`.

PowerShell lub CmdExec?

Wykorzystaj Proxy i Credential.

SSISDB?

Skorzystaj z modelu bezpieczeństwa katalogu.

Dopiero kiedy konto rzeczywiście potrzebuje pełnej kontroli nad instancją, `sysadmin` staje się uzasadnionym wyborem.

Bo dobrze zaprojektowane bezpieczeństwo nie polega na tym, żeby użytkownik mógł zrobić wszystko.

Polega na tym, żeby mógł zrobić **dokładnie to, czego potrzebuje — i nic więcej**.

> Najpierw zdefiniuj operację. Potem zaprojektuj dostęp. Nigdy odwrotnie.
