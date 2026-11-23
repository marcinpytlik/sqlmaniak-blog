---
title: "Permissions Auditing: Who, What, and When?"
date: 2025-10-20
slug: audyt-uprawnien
tags: [SQLServer, Security, Audit, Compliance, DBA]
draft: false
---

Trust is good, but `SERVER AUDIT` is better. Auditing helps you find out who granted, revoked, or changed permissions in your database. You do not need third-party tools: SQL Server already includes the necessary functionality. A few statements — `CREATE SERVER AUDIT` and `CREATE DATABASE AUDIT SPECIFICATION` — can establish an audit trail.

> “Without a log, there is no evidence. Without evidence, there is no security.”

## Why audit?

Permissions are power, and power should leave a trace. In environments with many administrators — or developers with sysadmin rights — it can be difficult to establish who changed what. Auditing helps restore accountability.

## Audit architecture

Auditing consists of three layers:

1. **Server Audit** defines where events are written: files, the Application Log, or the Security Log.
2. **Database Audit Specification** defines which actions are recorded in a particular database.
3. **Server Audit Specification** tracks server-level events, such as `SERVER_PRINCIPAL_CHANGE_GROUP`.

One `SERVER AUDIT` can serve multiple specifications, allowing you to centralize audit-event collection.

## Practical example

First, create an audit at the instance level:

```sql
CREATE SERVER AUDIT Audit_Uprawnienia
TO FILE (FILEPATH = 'C:\SQLAudit\', MAXSIZE = 100 MB, ROLLOVER_ON_FILE_CLOSE = ON)
WITH (ON_FAILURE = CONTINUE);
GO

ALTER SERVER AUDIT Audit_Uprawnienia
WITH (STATE = ON);
GO
```

Next, configure permission-change auditing for a specific database:

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

Statements such as `GRANT`, `DENY`, `REVOKE`, and `ALTER ROLE ... ADD MEMBER` can be captured when the relevant action groups are configured.

## Reading audit logs

You can read the audit files using `sys.fn_get_audit_file`:

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

The results show who performed an audited action, when it happened, and which object it involved. For longer retention, you can import events into a dedicated database such as `DBA_AuditLogs` and visualize them with Grafana or Power BI.

## Bonus: auditing logins

You can extend the configuration to monitor login attempts:

```sql
CREATE SERVER AUDIT SPECIFICATION Audit_Logowania
FOR SERVER AUDIT Audit_Uprawnienia
    ADD (FAILED_LOGIN_GROUP),
    ADD (SUCCESSFUL_LOGIN_GROUP)
WITH (STATE = ON);
GO
```

This allows you to see not only who changed something, but also who tried to access the system.

## Good practices

- Store audit logs on a separate disk or protected network resource.
- Archive audit logs regularly, especially in environments with many users.
- Monitor audit status with `sys.dm_server_audit_status` to detect unexpected disablement.
- Combine auditing with **Policy-Based Management** and **SQL Agent Alerts** to receive timely notifications.

## End-to-end verification (hands-on, 5–10 minutes)

Here is a quick test: create an object and a user, grant and revoke permissions, change role membership, and then inspect the audit trail.

> Prerequisites: `SERVER AUDIT Audit_Uprawnienia` and `DATABASE AUDIT SPECIFICATION Audit_Uprawnienia_DB` are enabled as shown above. The audit path is `C:\SQLAudit\`.

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

### What should you see?

- Entries for `GRANT SELECT`, `REVOKE SELECT`, and `ALTER ROLE ... ADD/DROP MEMBER`.
- The `server_principal_name` column identifies the login that executed the operation.
- `succeeded = 1` indicates a successful operation; `0` indicates a failure.

### Quick alert: Is auditing alive?

To check audit health from a SQL Agent job every five minutes, add a T-SQL step:

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

Connect this step to a SQL Agent alert (error number 50001) and send a notification by email, SNMP, or Teams.

---

Trust ends where lack of visibility begins. Auditing is your mirror: it shows who really pulls the levers.

Demo repository:
👉 [github.com/marcinpytlik/SQLManiak/tree/master/labs/07-security/PBM_Audit](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/07-security/PBM_Audit)
