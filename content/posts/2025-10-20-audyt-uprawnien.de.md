---
title: "Berechtigungsüberwachung: Wer, was und wann?"
date: 2025-10-20
slug: audyt-uprawnien
tags: [SQLServer, Security, Audit, Compliance, DBA]
draft: false
---

Vertrauen ist gut, aber `SERVER AUDIT` ist besser. Mit Auditing kannst du nachvollziehen, wer Berechtigungen in deiner Datenbank erteilt, entzogen oder geändert hat. Zusätzliche Werkzeuge von Drittanbietern sind nicht erforderlich: SQL Server bringt die Funktionen bereits mit. Wenige Anweisungen — `CREATE SERVER AUDIT` und `CREATE DATABASE AUDIT SPECIFICATION` — schaffen eine Überwachungsspur.

> „Ohne Protokoll gibt es keinen Beweis. Ohne Beweis gibt es keine Sicherheit.“

## Warum Auditing?

Berechtigungen bedeuten Macht, und Macht sollte Spuren hinterlassen. In Umgebungen mit vielen Administratoren — oder Entwicklern mit Sysadmin-Rechten — lässt sich oft schwer feststellen, wer was geändert hat. Auditing schafft Nachvollziehbarkeit und Verantwortlichkeit.

## Architektur der Überwachung

Die Überwachung besteht aus drei Ebenen:

1. **Server Audit** definiert, wohin Ereignisse geschrieben werden: in Dateien, das Application Log oder das Security Log.
2. **Database Audit Specification** legt fest, welche Aktionen in einer bestimmten Datenbank erfasst werden.
3. **Server Audit Specification** überwacht serverweite Ereignisse, beispielsweise `SERVER_PRINCIPAL_CHANGE_GROUP`.

Ein `SERVER AUDIT` kann von mehreren Spezifikationen verwendet werden. So lässt sich die Sammlung von Audit-Ereignissen zentralisieren.

## Praxisbeispiel

Erstelle zuerst ein Audit auf Instanzebene:

```sql
CREATE SERVER AUDIT Audit_Uprawnienia
TO FILE (FILEPATH = 'C:\SQLAudit\', MAXSIZE = 100 MB, ROLLOVER_ON_FILE_CLOSE = ON)
WITH (ON_FAILURE = CONTINUE);
GO

ALTER SERVER AUDIT Audit_Uprawnienia
WITH (STATE = ON);
GO
```

Konfiguriere anschließend die Überwachung von Berechtigungsänderungen für eine Datenbank:

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

Anweisungen wie `GRANT`, `DENY`, `REVOKE` und `ALTER ROLE ... ADD MEMBER` können erfasst werden, sofern die entsprechenden Aktionsgruppen konfiguriert sind.

## Audit-Protokolle lesen

Die Audit-Dateien lassen sich über `sys.fn_get_audit_file` auslesen:

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

Die Ergebnisse zeigen, wer eine überwachte Aktion durchgeführt hat, wann sie stattfand und welches Objekt betroffen war. Für eine längere Aufbewahrung kannst du Ereignisse in eine separate Datenbank wie `DBA_AuditLogs` importieren und mit Grafana oder Power BI visualisieren.

## Bonus: Anmeldeversuche überwachen

Du kannst die Konfiguration um die Überwachung von Anmeldungen erweitern:

```sql
CREATE SERVER AUDIT SPECIFICATION Audit_Logowania
FOR SERVER AUDIT Audit_Uprawnienia
    ADD (FAILED_LOGIN_GROUP),
    ADD (SUCCESSFUL_LOGIN_GROUP)
WITH (STATE = ON);
GO
```

So siehst du nicht nur, wer etwas geändert hat, sondern auch, wer versucht hat, auf das System zuzugreifen.

## Bewährte Vorgehensweisen

- Speichere Audit-Protokolle auf einem separaten Datenträger oder einer geschützten Netzwerkressource.
- Archiviere die Protokolle regelmäßig, besonders bei vielen Benutzern.
- Überwache den Audit-Status mit `sys.dm_server_audit_status`, damit eine unerwartete Deaktivierung auffällt.
- Kombiniere Auditing mit **Policy-Based Management** und **SQL Agent Alerts**, um rechtzeitig Benachrichtigungen zu erhalten.

## Ende-zu-Ende-Prüfung (Praxis, 5–10 Minuten)

Hier ist ein kurzer Test: Erstelle ein Objekt und einen Benutzer, erteile und entziehe Berechtigungen, ändere die Rollenmitgliedschaft und prüfe anschließend das Audit-Protokoll.

> Voraussetzungen: `SERVER AUDIT Audit_Uprawnienia` und `DATABASE AUDIT SPECIFICATION Audit_Uprawnienia_DB` sind wie oben aktiviert. Der Audit-Pfad lautet `C:\SQLAudit\`.

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

### Was solltest du sehen?

- Einträge für `GRANT SELECT`, `REVOKE SELECT` und `ALTER ROLE ... ADD/DROP MEMBER`.
- Die Spalte `server_principal_name` zeigt das Login, das die Operation ausgeführt hat.
- `succeeded = 1` kennzeichnet erfolgreiche Operationen; `0` steht für Fehler.

### Schneller Alarm: Läuft das Auditing?

Um den Zustand alle fünf Minuten über einen SQL-Agent-Job zu prüfen, füge einen T-SQL-Schritt hinzu:

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

Verknüpfe diesen Schritt mit einem SQL-Agent-Alert (Fehlernummer 50001) und versende eine Nachricht per E-Mail, SNMP oder Teams.

---

Vertrauen endet dort, wo die Transparenz fehlt. Auditing ist dein Spiegel: Es zeigt, wer tatsächlich die Hebel bewegt.

Demo-Repository:
👉 [github.com/marcinpytlik/SQLManiak/tree/master/labs/07-security/PBM_Audit](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/07-security/PBM_Audit)
