---
title: "Strangler Pattern dla bazy danych: jak wygaszać stary model bez wielkiego przełączenia"
date: 2026-09-30T00:01:00+02:00
slug: "strangler-pattern-baza-danych"
description: "Jak stopniowo zastępować stary model danych nowym bez jednego ryzykownego momentu migracji."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - schema evolution
  - strangler pattern
  - migracja danych
  - database DevOps
draft: false
---

# Strangler Pattern dla bazy danych: jak wygaszać stary model bez wielkiego przełączenia

Po Feature Flag naturalny krok to pytanie: **jak wycofać stary model, nie robiąc jednego wielkiego przełączenia?**

Jednym z podejść jest Strangler Pattern — nowa część systemu stopniowo przejmuje odpowiedzialność za kolejne operacje, aż stara struktura przestaje być potrzebna.

> Nie migruj wszystkiego naraz. Przejmuj odpowiedzialność kawałek po kawałku.

## Przykład

Stary model:

```sql
CREATE TABLE dbo.Customer
(
    CustomerId int NOT NULL PRIMARY KEY,
    Name nvarchar(200) NOT NULL,
    AddressText nvarchar(500) NULL
);
```

Nowy model:

```sql
CREATE TABLE dbo.CustomerAddress
(
    CustomerAddressId bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
    CustomerId int NOT NULL,
    AddressLine1 nvarchar(200) NOT NULL,
    City nvarchar(100) NOT NULL,
    PostalCode nvarchar(20) NULL
);
```

## Etap 1 — nowe zapisy

Najpierw kierujemy nowe operacje do nowego modelu. Stary pozostaje kompatybilny.

Możemy przez pewien czas utrzymywać:

- dual-write,
- zapis do nowego modelu i synchronizację wstecz,
- kolejkę zdarzeń aktualizujących starszą strukturę.

## Etap 2 — nowe odczyty

Następnie wybrane odczyty przechodzą do nowej tabeli. Feature Flag pozwala ograniczyć zakres.

Najpierw można wykonać shadow read i porównywać wyniki bez wpływu na użytkownika.

## Etap 3 — izolacja starego modelu

Stara tabela nie powinna być już używana bezpośrednio przez aplikacje.

Pomocne są:

- widoki zgodności,
- procedury składowane jako warstwa dostępu,
- osobny schemat `legacy`,
- monitoring zapytań trafiających do starego obiektu.

## Etap 4 — wygaszenie

Stary model usuwamy dopiero wtedy, gdy mamy dowód, że:

- nie ma aktywnych odczytów,
- nie ma aktywnych zapisów,
- backfill zakończył się poprawnie,
- integracje zostały przełączone,
- rollback nie wymaga już starej struktury.

## Największe ryzyko

Strangler Pattern nie działa, jeśli stary i nowy model przez długi czas stają się równorzędnymi źródłami prawdy.

Trzeba jasno określić, który model jest źródłem prawdy na każdym etapie migracji.

## Podsumowanie

Strangler Pattern pozwala zamienić jedną dużą migrację na serię małych, kontrolowanych przejęć odpowiedzialności.

Relacyjny Renesans nie polega na rewolucji. Polega na tym, żeby stary model spokojnie przestał być potrzebny.