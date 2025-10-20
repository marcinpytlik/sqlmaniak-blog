---
title: "Audyt uprawnień – kto, co i kiedy?"
date: 2025-10-20
slug: audyt-uprawnien
tags: [SQLServer, Security, Audit, Compliance, DBA]
draft: false
---

Zaufanie jest dobre, ale `SERVER AUDIT` jest lepszy.  
Audyt pozwala Ci wiedzieć, kto nadał, odebrał lub zmienił uprawnienia w Twojej bazie.  
Nie potrzebujesz narzędzi firm trzecich — wszystko masz wbudowane w SQL Server.  
Wystarczy kilka poleceń: `CREATE SERVER AUDIT`, `CREATE DATABASE AUDIT SPECIFICATION`, i masz pełny ślad bezpieczeństwa.

> „Bez logu nie ma dowodu. Bez dowodu nie ma bezpieczeństwa.”

## Dlaczego audyt?

Uprawnienia to władza. A każda władza powinna zostawiać ślady.  
W systemach z wieloma administratorami (lub z zespołem deweloperów z prawami sysadmina) często nie sposób ustalić, kto co zmienił.  
Audyt pozwala przywrócić porządek i odpowiedzialność.

## Architektura audytu

Audyt składa się z trzech warstw:

1. **Server Audit** – definiuje, gdzie będą zapisywane zdarzenia (plik, Application Log, Security Log).  
2. **Database Audit Specification** – określa, które akcje w danej bazie są rejestrowane.  
3. **Server Audit Specification** – śledzi zdarzenia globalne, np. `SERVER_PRINCIPAL_CHANGE_GROUP`.

Ważne: jeden `SERVER AUDIT` może być używany przez wiele specyfikacji, więc możesz budować centralny punkt zbierania zdarzeń.

## Praktyczny przykład

Zacznijmy od utworzenia audytu na poziomie instancji:

```sql
CREATE SERVER AUDIT Audit_Uprawnienia
TO FILE (FILEPATH = 'C:\SQLAudit\', MAXSIZE = 100 MB, ROLLOVER_ON_FILE_CLOSE = ON)
WITH (ON_FAILURE = CONTINUE);
GO

ALTER SERVER AUDIT Audit_Uprawnienia
WITH (STATE = ON);
GO
```

Teraz skonfigurujmy śledzenie zmian uprawnień w konkretnej bazie:

```sql
USE AdventureWorks2022;
GO

CREATE DATABASE AUDIT SPECIFICATION Audit_Uprawnienia_DB
FOR SERVER AUDIT Audit_Uprawnienia
    ADD (SCHEMA_OBJECT_PERMISSION_CHANGE_GROUP),
    ADD (DATABASE_PRINCIPAL_CHANGE_GROUP),
    ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP)
WITH (STATE = ON);
GO
```

Każde polecenie `GRANT`, `DENY`, `REVOKE`, czy `ALTER ROLE ... ADD MEMBER` zostanie zarejestrowane.

## Odczyt logów audytu

Odczyt jest prosty — wszystko znajduje się w widoku `sys.fn_get_audit_file`:

```sql
SELECT
    event_time,
    server_principal_name AS [Kto],
    database_name AS [Baza],
    object_name AS [Obiekt],
    statement AS [Polecenie],
    action_id AS [Akcja]
FROM sys.fn_get_audit_file('C:\SQLAudit\*', DEFAULT, DEFAULT)
ORDER BY event_time DESC;
```

Wynik pokaże dokładnie, kto zmienił jakie uprawnienie, kiedy i na jakim obiekcie.  
Jeśli masz logów z kilku dni — możesz zaimportować je do dedykowanej bazy np. `DBA_AuditLogs` i wizualizować w Grafanie lub Power BI.

## Bonus – audyt zmian logowania

Jeśli chcesz pójść dalej, możesz dodać również monitorowanie logowań:

```sql
CREATE SERVER AUDIT SPECIFICATION Audit_Logowania
FOR SERVER AUDIT Audit_Uprawnienia
    ADD (FAILED_LOGIN_GROUP),
    ADD (SUCCESSFUL_LOGIN_GROUP)
WITH (STATE = ON);
GO
```

W ten sposób widzisz nie tylko kto coś zmienił, ale też kto próbował dostać się do systemu.

## Dobre praktyki

- Zapisuj logi na osobnym dysku lub zasobie sieciowym tylko do odczytu.  
- Regularnie archiwizuj logi audytu, zwłaszcza przy dużej liczbie użytkowników.  
- Monitoruj stan audytu — `sys.dm_server_audit_status` pokaże, czy nie został przypadkiem wyłączony.  
- Połącz audyt z **Policy-Based Management** i **SQL Agent Alerts** – będziesz wiedzieć natychmiast, gdy ktoś spróbuje coś zmienić.

## Weryfikacja działania (hands-on, 5–10 min)

Poniżej szybki test end-to-end: tworzymy obiekt i użytkownika, nadajemy/odbieramy uprawnienia, dodajemy do roli – a potem sprawdzamy dziennik audytu.

> Założenia: masz włączony `SERVER AUDIT Audit_Uprawnienia` oraz `DATABASE AUDIT SPECIFICATION Audit_Uprawnienia_DB` (jak wyżej). Ścieżka audytu to `C:\SQLAudit\`.

```sql
/* 0) Parametry i sanity check */
DECLARE @AuditPath NVARCHAR(4000) = N'C:\SQLAudit\*';

SELECT audit_id, name, status_desc, queue_delay, on_failure_desc, file_path
FROM sys.dm_server_audit_status;

/* 1) Środowisko testowe */
USE AdventureWorks2022;
GO
IF OBJECT_ID('dbo.AuditDemo','U') IS NOT NULL DROP TABLE dbo.AuditDemo;
CREATE TABLE dbo.AuditDemo(Id int IDENTITY(1,1) PRIMARY KEY, Payload nvarchar(100));

/* 1a) Login + User (sandbox) */
IF SUSER_ID('AuditTestLogin') IS NOT NULL DROP LOGIN AuditTestLogin;
CREATE LOGIN AuditTestLogin WITH PASSWORD = 'Str0ng!Pass#2025', CHECK_POLICY = OFF; -- lab only
GO
USE AdventureWorks2022;
GO
IF USER_ID('AuditTestUser') IS NOT NULL DROP USER AuditTestUser;
CREATE USER AuditTestUser FOR LOGIN AuditTestLogin;

/* 2) Akcje, które powinny wpaść do audytu */
-- GRANT na obiekcie
GRANT SELECT ON dbo.AuditDemo TO AuditTestUser;

-- Dodanie do roli db_datareader
ALTER ROLE db_datareader ADD MEMBER AuditTestUser;

-- REVOKE uprawnienia
REVOKE SELECT ON dbo.AuditDemo FROM AuditTestUser;

-- Usunięcie z roli
ALTER ROLE db_datareader DROP MEMBER AuditTestUser;

/* (opcjonalnie) Zmiana definicji uprawnień na schemacie/obiekcie:
DENY INSERT ON dbo.AuditDemo TO AuditTestUser;
REVOKE INSERT ON dbo.AuditDemo FROM AuditTestUser;
*/

/* 3) Daj silnikowi chwilę na spłynięcie zdarzeń do pliku audytu */
WAITFOR DELAY '00:00:02';

/* 4) Odczyt logu audytu: kto/co/kiedy + fragment polecenia */
SELECT
    event_time,
    succeeded,
    server_instance_name,
    server_principal_name   AS [Kto (login)],
    database_principal_name AS [Kto (user)],
    database_name           AS [Baza],
    schema_name             AS [Schemat],
    object_name             AS [Obiekt],
    action_id               AS [Akcja],
    statement               AS [Polecenie]
FROM sys.fn_get_audit_file(@AuditPath, DEFAULT, DEFAULT)
WHERE database_name = DB_NAME()
  AND (
        statement LIKE '%GRANT%' OR
        statement LIKE '%REVOKE%' OR
        statement LIKE '%ALTER ROLE%' OR
        action_id IN ('G','R')
      )
ORDER BY event_time DESC;
```

### Co powinieneś zobaczyć?
- Wiersze z `GRANT SELECT`, `REVOKE SELECT` oraz `ALTER ROLE ... ADD/DROP MEMBER`.
- Kolumna `server_principal_name` wskaże konto, pod którym wykonano operację (Twoja sesja).
- `succeeded = 1` dla udanych operacji; nieudane dostaniesz z `0`.

### Szybki alert „czy audyt żyje?”
Jeśli chcesz mieć heartbeat w SQL Agent (co 5 min), dodaj prosty krok T-SQL:

```sql
IF NOT EXISTS (
    SELECT 1
    FROM sys.dm_server_audit_status
    WHERE status = 1 AND name = N'Audit_Uprawnienia'
)
BEGIN
    THROW 50001, 'SERVER AUDIT Audit_Uprawnienia jest WYŁĄCZONY lub niedostępny', 1;
END
```

Powiąż ten krok z Alertem agenta (Error Number = 50001) i wyślij mail/SNMP/Teams.

---

Zaufanie kończy się tam, gdzie zaczyna się nieświadomość.  
Audyt to Twoje lustro – pokazuje, kto naprawdę pociąga za dźwignie.

Repozytorium demonstracyjne:  
👉 [github.com/marcinpytlik/SQLManiak/tree/master/labs/07-security/PBM_Audit](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/07-security/PBM_Audit)
