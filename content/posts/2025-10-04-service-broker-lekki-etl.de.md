---
title: "Service Broker als schlankes ETL: von der Rechnungswarteschlange zur Faktentabelle"
date: "2025-10-04"
slug: "service-broker-schlankes-etl"
draft: false
description: "Asynchrone Aktualisierung von Berichten: Nach dem Einfügen einer Rechnung gelangt eine Nachricht in eine Warteschlange und aktualisiert im Hintergrund eine Faktentabelle."
tags: ["SQL Server","Query Store","PSP","Performance","Tuning"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/service-broker-lekki-etl.png"
---

Lead
----
Deine Berichte dürfen das OLTP-System nicht ausbremsen? Service Broker ist wie ein Postbote innerhalb der Datenbank: schnell, lokal und ohne SSIS.

## Architektur
- Ein INSERT in `ERP.dbo.Invoice` sendet eine Nachricht an `ReportingQueue`.  
- Die Aktivierung der Serviceprozedur überführt die Daten in `Reporting.dbo.FactInvoice`.

## Minimales Beispiel
```sql
-- Włącz SB
ALTER DATABASE ERP SET ENABLE_BROKER WITH ROLLBACK IMMEDIATE;

-- Kontrakt i typ wiadomości
CREATE MESSAGE TYPE [//InvoiceCreated] VALIDATION = WELL_FORMED_XML;
CREATE CONTRACT [//ReportingContract] ([//InvoiceCreated] SENT BY INITIATOR);

-- Kolejki i usługi
CREATE QUEUE ReportingQueue;
CREATE SERVICE [//ReportingService] ON QUEUE ReportingQueue ([//ReportingContract]);
```

Aktivierungsprozedur (Pseudocode):
```sql
CREATE OR ALTER PROC dbo.OnInvoiceMessage AS
BEGIN
  SET NOCOUNT ON;
  DECLARE @h UNIQUEIDENTIFIER, @msg XML;
  RECEIVE TOP(1) @h=conversation_handle, @msg=message_body FROM ReportingQueue;
  IF @h IS NULL RETURN;
  INSERT Reporting.dbo.FactInvoice(...) SELECT ... FROM OPENXML(@msg, 'Invoice', 2) WITH (...);
  END CONVERSATION @h;
END
```
Aktivierung:
```sql
ALTER QUEUE ReportingQueue WITH STATUS=ON, ACTIVATION (STATUS=ON, PROCEDURE_NAME=dbo.OnInvoiceMessage, MAX_QUEUE_READERS=5, EXECUTE AS OWNER);
```

## Vorteile
- Lang laufende Berichte blockieren den OLTP-Ablauf nicht.  
- Volle Kontrolle und transaktionale Verarbeitung in SQL Server.  
- Die Datenbanken können getrennt werden (ERP und Reporting).

## Worauf zu achten ist
- Größe der Warteschlange und Verarbeitungsverzögerung.  
- Verarbeitungsfehler und Behandlung einer Dead-Letter-Queue (DLQ).  
- Idempotenz bei einer Verarbeitung nach dem At-least-once-Prinzip.
