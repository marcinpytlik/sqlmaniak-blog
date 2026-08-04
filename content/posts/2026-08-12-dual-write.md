---
title: "Dual Write w bazie danych: pomocny most czy źródło niespójności?"
date: 2026-08-12T00:01:00+02:00
slug: "dual-write-baza-danych"
description: "Jak bezpiecznie stosować równoległy zapis do starego i nowego modelu podczas migracji schematu SQL Server."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - dual write
  - migracja danych
  - transakcje
  - spójność danych
draft: false
---

# Dual Write w bazie danych: pomocny most czy źródło niespójności?

Podczas ewolucji schematu często pojawia się okres, w którym stara i nowa struktura muszą działać równolegle. Aplikacja V1 zapisuje dane do starej tabeli, a aplikacja V2 oczekuje już nowego modelu.

Jednym z rozwiązań jest **Dual Write**, czyli zapis tej samej operacji biznesowej w dwóch miejscach.

Wzorzec brzmi prosto:

1. zapisz dane do starego modelu,
2. zapisz dane do nowego modelu,
3. utrzymuj oba modele do zakończenia migracji.

Największy problem polega na tym, że dwa zapisy tworzą dwa miejsca potencjalnej awarii.

> Dual Write nie jest problemem wtedy, gdy oba zapisy są atomowe. Problem zaczyna się wtedy, gdy jeden z nich może zakończyć się powodzeniem, a drugi błędem.

## Przykład migracji adresu

Stary model przechowuje adres w kolumnie `Customers.AddressText`. Nowy model używa tabeli `CustomerAddresses`.

Tymczasowa procedura może zapisywać oba modele:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_CustomerAddress_Save
    @CustomerId   int,
    @AddressLine1 nvarchar(200),
    @PostalCode   nvarchar(20),
    @City         nvarchar(100)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRANSACTION;

    UPDATE dbo.Customers
    SET AddressText = CONCAT(
        @AddressLine1,
        N', ',
        @PostalCode,
        N' ',
        @City
    )
    WHERE CustomerId = @CustomerId;

    MERGE dbo.CustomerAddresses AS target
    USING
    (
        SELECT
            @CustomerId AS CustomerId,
            @AddressLine1 AS AddressLine1,
            @PostalCode AS PostalCode,
            @City AS City
    ) AS source
        ON target.CustomerId = source.CustomerId
       AND target.IsPrimary = 1
    WHEN MATCHED THEN
        UPDATE SET
            AddressLine1 = source.AddressLine1,
            PostalCode = source.PostalCode,
            City = source.City
    WHEN NOT MATCHED THEN
        INSERT
        (
            CustomerId,
            AddressType,
            AddressLine1,
            PostalCode,
            City,
            IsPrimary
        )
        VALUES
        (
            source.CustomerId,
            'Other',
            source.AddressLine1,
            source.PostalCode,
            source.City,
            1
        );

    COMMIT;
END;
```

Oba zapisy są objęte jedną transakcją SQL Server. Jeżeli drugi zapis zakończy się błędem, pierwszy również zostanie wycofany.

W praktyce zamiast `MERGE` wiele zespołów wybiera jawne `UPDATE` i `INSERT`, ponieważ łatwiej kontrolować współbieżność oraz zachowanie w złożonych scenariuszach.

## Najgorszy wariant: dwa niezależne wywołania

Niebezpieczny kod aplikacji może wyglądać logicznie:

```text
UPDATE starego modelu
COMMIT

INSERT do nowego modelu
COMMIT
```

Jeżeli pierwszy krok się powiedzie, a drugi zakończy błędem, modele będą się różnić. Ponowienie całej operacji może z kolei wykonać pierwszy zapis drugi raz.

Jeszcze trudniejszy przypadek występuje wtedy, gdy jeden zapis trafia do SQL Servera, a drugi do zewnętrznej usługi lub brokera wiadomości. Nie mamy wtedy jednej lokalnej transakcji obejmującej oba zasoby.

W takiej sytuacji lepszym rozwiązaniem może być:

- Transactional Outbox,
- kolejka zmian,
- Change Data Capture,
- asynchroniczny proces synchronizacji,
- jeden model jako źródło prawdy.

## Który model jest źródłem prawdy?

Dual Write musi mieć jasno określony kierunek.

Możliwe warianty:

### Stary model jest źródłem prawdy

Nowa struktura jest aktualizowana wtórnie. To bezpieczne na początku migracji, gdy większość ruchu nadal korzysta z V1.

### Nowy model jest źródłem prawdy

Stara struktura jest utrzymywana wyłącznie dla kompatybilności raportów lub aplikacji V1. Jest to naturalny etap przed usunięciem starego modelu.

### Oba modele są równorzędne

To najbardziej ryzykowna sytuacja. Jeżeli oba modele mogą być niezależnie modyfikowane, potrzebujemy reguł rozwiązywania konfliktów. W praktyce często okazuje się, że powstały dwa systemy źródłowe zamiast kontrolowanej migracji.

## Walidacja zgodności

W okresie Dual Write należy regularnie porównywać modele.

```sql
SELECT
    c.CustomerId,
    LegacyAddress = c.AddressText,
    NewAddress = CONCAT(
        ca.AddressLine1,
        N', ',
        ca.PostalCode,
        N' ',
        ca.City
    )
FROM dbo.Customers AS c
JOIN dbo.CustomerAddresses AS ca
    ON ca.CustomerId = c.CustomerId
   AND ca.IsPrimary = 1
WHERE ISNULL(c.AddressText, N'')
   <> ISNULL(
        CONCAT(
            ca.AddressLine1,
            N', ',
            ca.PostalCode,
            N' ',
            ca.City
        ),
        N''
   );
```

Taki raport zgodności powinien być częścią monitoringu migracji, a nie jednorazowym testem.

Warto mierzyć:

- liczbę niespójnych rekordów,
- czas od ostatniej synchronizacji,
- liczbę błędów zapisu do każdego modelu,
- liczbę ponowień,
- udział ruchu korzystającego z V1 i V2.

## Idempotencja

Operacje wykonywane w okresie migracji powinny być odporne na ponowienie. Pomagają w tym:

- unikalne klucze biznesowe,
- `IdempotencyKey`,
- `UPSERT` realizowany w kontrolowany sposób,
- tabela przetworzonych komunikatów,
- zapis wersji rekordu,
- jawne identyfikatory operacji.

Przykład tabeli operacji:

```sql
CREATE TABLE dbo.ProcessedRequests
(
    RequestId uniqueidentifier NOT NULL,
    ProcessedAt datetime2(0) NOT NULL,
    ResultCode varchar(30) NOT NULL,

    CONSTRAINT PK_ProcessedRequests
        PRIMARY KEY (RequestId)
);
```

Przed wykonaniem zapisu aplikacja lub procedura może sprawdzić, czy żądanie zostało już obsłużone.

## Jak długo utrzymywać Dual Write?

Najkrócej, jak to możliwe.

Dual Write jest mechanizmem przejściowym. Im dłużej działa, tym większe ryzyko, że stanie się trwałym elementem architektury. Każda poprawka musi wtedy uwzględniać dwa modele, a zespół traci pewność, który z nich jest właściwy.

Przed wdrożeniem warto określić warunki wyłączenia:

- wszystkie instancje aplikacji działają w wersji V2,
- migracja historycznych danych została zakończona,
- raport zgodności przez określony czas zwraca zero różnic,
- stare raporty i integracje zostały przełączone,
- monitoring potwierdza brak odwołań do starego modelu.

## Kiedy stosować?

Dual Write może być dobrym rozwiązaniem, gdy:

- oba zapisy znajdują się w tej samej bazie i transakcji,
- okres zgodności jest krótki,
- potrzebujemy bezprzestojowego przełączenia,
- mamy raport porównujący oba modele,
- jasno określiliśmy źródło prawdy.

## Kiedy unikać?

Należy zachować szczególną ostrożność, gdy:

- zapisy trafiają do różnych systemów,
- nie można zapewnić atomowości,
- oba modele mogą być niezależnie edytowane,
- nie ma mechanizmu ponawiania i idempotencji,
- nikt nie określił daty usunięcia rozwiązania przejściowego.

## Podsumowanie

Dual Write jest użytecznym mostem podczas ewolucji schematu. Nie powinien być jednak traktowany jak niewinna instrukcja „zapisz dwa razy”.

Bezpieczny Dual Write wymaga:

- atomowości,
- jednego źródła prawdy,
- idempotencji,
- monitoringu niespójności,
- krótkiego okresu działania,
- jasno zaplanowanego wyłączenia.

Najważniejsze pytanie nie brzmi:

> Czy potrafimy zapisać dane do dwóch miejsc?

Brzmi:

> Co zrobimy, kiedy jeden z tych zapisów się nie powiedzie?
