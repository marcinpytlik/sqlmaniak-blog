---
title: "Service Broker jako lekki ETL: kolejka faktur → tabela faktów"
date: "2025-10-04"
slug: "service-broker-lekki-etl"
draft: false
description: "Projektowanie asynchronicznego zasilania raportów: po wstawieniu faktury komunikat trafia do kolejki i w tle aktualizuje tabelę faktów."
tags: ["SQL Server", "Service Broker", "ETL", "Asynchroniczność", "Reporting"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/service-broker-lekki-etl.png"
canonical: "https://sqlmaniak.blog/service-broker-lekki-etl"
---

Lead
----
Masz raporty, które nie mogą dławić OLTP? Service Broker jest jak listonosz w tej samej bazie: szybko, lokalnie, bez SSIS.

## Schemat
- INSERT do `ERP.dbo.Invoice` → wysyłka komunikatu do kolejki `ReportingQueue`.  
- Aktywacja procedury serwisowej → transformacja do `Reporting.dbo.FactInvoice`.

## Minimalny przykład
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

Procedura aktywacji (pseudokod):
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
Aktywacja:
```sql
ALTER QUEUE ReportingQueue WITH STATUS=ON, ACTIVATION (STATUS=ON, PROCEDURE_NAME=dbo.OnInvoiceMessage, MAX_QUEUE_READERS=5, EXECUTE AS OWNER);
```

## Zalety
- Brak blokad na długim raporcie.  
- Pełna kontrola i transakcyjność w SQL.  
- Można rozdzielić bazy (ERP vs Reporting).

## Na co uważać
- Rozmiar kolejki i monitoring „poślizgu”.  
- Błędy przetwarzania → DLQ (dead‑letter).  
- Idempotencja – insert „at‑least once”.
