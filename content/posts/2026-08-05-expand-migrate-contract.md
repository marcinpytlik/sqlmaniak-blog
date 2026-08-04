---
title: "Expand–Migrate–Contract: jak zmieniać schemat bez zatrzymywania aplikacji"
date: 2026-08-05T00:01:00+02:00
slug: "expand-migrate-contract-ewolucja-schematu"
description: "Praktyczny wzorzec bezpiecznej ewolucji schematu SQL Server: rozszerzenie modelu, migracja danych, okres zgodności, walidacja i usunięcie starej struktury."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - projektowanie baz danych
  - ewolucja schematu
  - deployment
  - migracja danych
draft: false
---

# Expand–Migrate–Contract: jak zmieniać schemat bez zatrzymywania aplikacji

Projektowanie nowej tabeli jest stosunkowo łatwe. Znacznie trudniejsze jest zmienianie tabeli, z której korzystają już aplikacje, raporty, procesy ETL oraz użytkownicy.

W środowisku laboratoryjnym możemy wykonać `ALTER TABLE`, poprawić kod i uruchomić wszystko ponownie. W systemie produkcyjnym przez pewien czas mogą jednak działać równolegle dwie wersje aplikacji. Jeden raport może nadal oczekiwać starej kolumny, a proces integracyjny może wykonywać się tylko raz dziennie i ujawnić problem dopiero wiele godzin po wdrożeniu.

Wzorzec **Expand–Migrate–Contract** pozwala rozłożyć zmianę na kontrolowane etapy:

1. **Expand** – dodajemy nową strukturę, ale nie usuwamy starej.
2. **Migrate** – przenosimy dane i ruch aplikacyjny.
3. **Validate** – sprawdzamy kompletność i rzeczywiste wykorzystanie starego modelu.
4. **Contract** – dopiero wtedy usuwamy starą strukturę.

Najważniejsza zasada brzmi:

> Zmiana schematu jest procesem wdrożeniowym, a nie pojedynczą instrukcją DDL.

## Przykładowy problem

Załóżmy, że pierwsza wersja systemu przechowuje adres klienta w jednej kolumnie:

```sql
CREATE TABLE dbo.Customers
(
    CustomerId   int IDENTITY(1,1) NOT NULL,
    CustomerName nvarchar(200) NOT NULL,
    AddressText  nvarchar(500) NULL,

    CONSTRAINT PK_Customers
        PRIMARY KEY (CustomerId)
);
```

Po pewnym czasie biznes chce:

- przechowywać kilka adresów,
- rozróżniać adres rozliczeniowy i wysyłkowy,
- filtrować klientów po mieście,
- integrować dane z firmą kurierską.

Naturalnym modelem docelowym jest osobna tabela adresów. Ryzykownym rozwiązaniem byłoby jednak natychmiastowe usunięcie `AddressText`.

## Etap 1: Expand

Najpierw dodajemy nową tabelę:

```sql
CREATE TABLE dbo.CustomerAddresses
(
    CustomerAddressId bigint IDENTITY(1,1) NOT NULL,
    CustomerId        int NOT NULL,
    AddressType       varchar(20) NOT NULL,
    AddressLine1      nvarchar(200) NOT NULL,
    PostalCode        nvarchar(20) NULL,
    City              nvarchar(100) NULL,
    CountryCode       char(2) NOT NULL,
    IsPrimary         bit NOT NULL,

    CONSTRAINT PK_CustomerAddresses
        PRIMARY KEY (CustomerAddressId),

    CONSTRAINT FK_CustomerAddresses_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customers(CustomerId)
);
```

Stara kolumna nadal istnieje. Oznacza to, że aplikacja V1 może działać bez zmian, a aplikacja V2 może być przygotowywana do korzystania z nowego modelu.

Zmiana rozszerzająca jest zwykle łatwiejsza do wdrożenia niż zmiana usuwająca. Dodanie tabeli nie łamie istniejącego kontraktu. Usunięcie kolumny już tak.

## Etap 2: Migrate

Dane należy przenieść do nowego modelu. Na małej tabeli wystarczy pojedynczy `INSERT ... SELECT`. Na dużej tabeli lepiej stosować partie.

```sql
WHILE 1 = 1
BEGIN
    ;WITH Batch AS
    (
        SELECT TOP (1000)
            c.CustomerId,
            c.AddressText
        FROM dbo.Customers AS c
        WHERE c.AddressText IS NOT NULL
          AND NOT EXISTS
          (
              SELECT 1
              FROM dbo.CustomerAddresses AS ca
              WHERE ca.CustomerId = c.CustomerId
          )
        ORDER BY c.CustomerId
    )
    INSERT INTO dbo.CustomerAddresses
    (
        CustomerId,
        AddressType,
        AddressLine1,
        CountryCode,
        IsPrimary
    )
    SELECT
        CustomerId,
        'Other',
        AddressText,
        'PL',
        1
    FROM Batch;

    IF @@ROWCOUNT = 0
        BREAK;
END;
```

Migracja partiami ogranicza:

- czas pojedynczej transakcji,
- wzrost logu transakcyjnego,
- długość blokad,
- ryzyko długiego rollbacku,
- wpływ na codzienną pracę systemu.

Proces powinien być idempotentny albo przynajmniej wznawialny. Ponowne uruchomienie nie może tworzyć duplikatów.

## Okres zgodności

Przez pewien czas stara i nowa wersja aplikacji mogą działać równolegle. Wtedy trzeba zdecydować, jak utrzymać spójność.

Możliwe rozwiązania to:

- tymczasowy dual write,
- jedna procedura zapisująca oba modele,
- widok zgodności,
- zatrzymanie zapisu V1 po przełączeniu wszystkich instancji aplikacji.

Dual write bywa użyteczny, ale zwiększa złożoność. Jeżeli zapis do jednej struktury powiedzie się, a do drugiej nie, powstaje niespójność. Dlatego oba zapisy powinny znaleźć się w jednej transakcji lokalnej.

## Walidacja przed usunięciem starego modelu

Nie należy usuwać kolumny tylko dlatego, że wdrożono nową aplikację. Potrzebne są dowody.

Najprostsza kontrola kompletności:

```sql
SELECT
    c.CustomerId,
    c.CustomerName,
    c.AddressText
FROM dbo.Customers AS c
WHERE c.AddressText IS NOT NULL
  AND NOT EXISTS
  (
      SELECT 1
      FROM dbo.CustomerAddresses AS ca
      WHERE ca.CustomerId = c.CustomerId
  );
```

Zapytanie powinno zwrócić zero wierszy.

Trzeba również sprawdzić zależności modułów:

```sql
SELECT
    ReferencingSchema = OBJECT_SCHEMA_NAME(d.referencing_id),
    ReferencingObject = OBJECT_NAME(d.referencing_id),
    d.referenced_entity_name
FROM sys.sql_expression_dependencies AS d
WHERE d.referenced_id = OBJECT_ID(N'dbo.Customers');
```

To nadal nie daje pełnej gwarancji. Dynamiczny SQL, kod aplikacji i zewnętrzne raporty mogą nie pojawić się w metadanych. W praktyce warto wykorzystać również Query Store, Extended Events, monitoring błędów aplikacji oraz analizę repozytoriów kodu.

## Etap 3: Contract

Dopiero po zakończeniu migracji i wycofaniu aplikacji V1 możemy usunąć starą strukturę:

```sql
ALTER TABLE dbo.Customers
    DROP COLUMN AddressText;
```

Przed tą operacją należy usunąć lub zmienić:

- procedury odwołujące się do kolumny,
- widoki zgodności,
- triggery,
- indeksy,
- raporty,
- procesy ETL,
- mapowania ORM.

Etap `Contract` powinien być osobnym wdrożeniem. Rozdzielenie go od etapu `Expand` daje czas na obserwację systemu i bezpieczne wycofanie kodu aplikacji.

## Rollback czy roll forward?

Wycofanie kodu nie zawsze oznacza możliwość wycofania migracji bazy. Jeżeli nowa aplikacja zapisała dane, których stary model nie potrafi reprezentować, powrót może oznaczać utratę informacji.

Dlatego warto wcześniej określić:

- do którego momentu możliwy jest rollback,
- kiedy przechodzimy na strategię roll forward,
- jak odtworzyć dane w przypadku niepełnej migracji,
- jakie metryki decydują o zatrzymaniu wdrożenia.

## Kiedy używać wzorca?

Expand–Migrate–Contract sprawdza się szczególnie wtedy, gdy:

- wdrożenie nie może wymagać długiego przestoju,
- aplikacja jest uruchomiona na wielu instancjach,
- schemat jest współdzielony przez raporty i integracje,
- migracja danych trwa długo,
- potrzebujemy możliwości kontrolowanego przełączenia.

## Koszty

Wzorzec nie jest darmowy. Przez pewien czas utrzymujemy dwa modele, dodatkowy kod zgodności i więcej kroków wdrożenia. Potrzebujemy też monitoringu oraz procedury sprzątania.

To jednak koszt kontrolowanej zmiany. Alternatywą jest wdrożenie typu „wszystko naraz”, w którym każdy ukryty konsument starej struktury może zatrzymać system.

## Podsumowanie

Dojrzała ewolucja schematu nie zaczyna się od pytania:

> Czy instrukcja `ALTER TABLE` się wykona?

Zaczyna się od pytań:

- Czy system będzie działał podczas zmiany?
- Czy obie wersje aplikacji pozostaną kompatybilne?
- Czy migrację można wznowić?
- Jak potwierdzimy kompletność danych?
- Kiedy usunięcie starego modelu będzie bezpieczne?

Expand–Migrate–Contract zamienia ryzykowną zmianę w serię małych, obserwowalnych i odwracalnych kroków. I właśnie dlatego jest jednym z podstawowych wzorców ewolucji relacyjnych baz danych.
