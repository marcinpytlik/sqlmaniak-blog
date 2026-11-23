---
title: "Service Broker as Lightweight ETL: Invoice Queue to Fact Table"
date: "2025-10-04"
slug: "service-broker-lightweight-etl"
draft: false
description: "Designing asynchronous reporting updates: after an invoice is inserted, a message enters a queue and updates a fact table in the background."
tags: ["SQL Server","Query Store","PSP","Performance","Tuning"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/service-broker-lekki-etl.png"
---

Lead
----
Do you have reports that must not slow down OLTP? Service Broker works like a mail carrier inside the database: fast, local, and without SSIS.

## Architecture
- An INSERT into `ERP.dbo.Invoice` sends a message to `ReportingQueue`.  
- Service procedure activation transforms the message into `Reporting.dbo.FactInvoice`.

## Minimal example
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

Activation procedure (pseudocode):
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
Activation:
```sql
ALTER QUEUE ReportingQueue WITH STATUS=ON, ACTIVATION (STATUS=ON, PROCEDURE_NAME=dbo.OnInvoiceMessage, MAX_QUEUE_READERS=5, EXECUTE AS OWNER);
```

## Benefits
- Long-running reports do not block the OLTP workflow.  
- Full control and transactional processing in SQL Server.  
- Databases can be separated (ERP vs. Reporting).

## Things to watch
- Queue size and processing lag.  
- Processing failures and dead-letter queue (DLQ) handling.  
- Idempotency for at-least-once message processing.
