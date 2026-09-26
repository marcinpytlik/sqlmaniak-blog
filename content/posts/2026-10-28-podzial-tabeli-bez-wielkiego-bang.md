---
title: "Podział tabeli bez Big Bang: jak rozdzielić jeden model na dwa"
date: 2026-10-28T00:01:00+01:00
slug: "podzial-tabeli-bez-big-bang"
description: "Jak bezpiecznie podzielić szeroką tabelę na dwie struktury bez jednorazowego przepisywania aplikacji i danych."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - schema evolution
  - normalizacja
  - migracja danych
  - database DevOps
draft: false
---

# Podział tabeli bez Big Bang: jak rozdzielić jeden model na dwa

Załóżmy, że przez lata tabela `Customer` urosła do kilkudziesięciu kolumn.

Część danych adresowych chcemy przenieść do osobnej tabeli.

## Nowa tabela

```sql
CREATE TABLE dbo.CustomerAddress
(
    CustomerId int NOT NULL,
    AddressType varchar(20) NOT NULL,
    AddressLine1 nvarchar(200) NOT NULL,
    City nvarchar(100) NOT NULL,
    PostalCode nvarchar(20) NULL,
    CONSTRAINT PK_CustomerAddress
        PRIMARY KEY (CustomerId, AddressType)
);
```

## Krok 1 — nowa struktura bez usuwania starej

Stare kolumny nadal istnieją. Nowa tabela jest rozszerzeniem modelu.

## Krok 2 — backfill

```sql
INSERT dbo.CustomerAddress
(
    CustomerId, AddressType, AddressLine1, City, PostalCode
)
SELECT
    CustomerId, 'PRIMARY', AddressLine1, City, PostalCode
FROM dbo.Customer
WHERE AddressLine1 IS NOT NULL;
```

Na dużych tabelach proces wykonujemy w batchach i zapisujemy checkpoint.

## Krok 3 — synchronizacja

W okresie przejściowym zmiana adresu musi trafić do obu modeli albo do jednego źródła prawdy z synchronizacją do drugiego.

## Krok 4 — przełączenie odczytu

Najpierw mała część ruchu, potem coraz większa.

Shadow read pozwala porównać stary i nowy wynik.

## Krok 5 — usunięcie starych kolumn

To ostatni etap, nie część pierwszego wdrożenia.

Przed Contract sprawdź:

- raporty,
- integracje,
- ETL,
- procedury,
- dynamiczny SQL,
- eksporty,
- narzędzia BI.

## Ryzyko semantyczne

Podział tabeli często zmienia nie tylko fizyczny schemat, ale również znaczenie danych.

Jeden adres może stać się wieloma adresami. Wtedy rollback do starego modelu może być stratny.

## Podsumowanie

Podział tabeli jest bezpieczny wtedy, gdy najpierw dodajemy nową reprezentację, potem przenosimy ruch, a dopiero na końcu usuwamy starą.