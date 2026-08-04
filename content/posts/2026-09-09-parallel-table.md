---
title: "Parallel Table: migracja do nowej tabeli bez ryzykownej przebudowy starej"
date: 2026-09-09T00:01:00+02:00
slug: "parallel-table-migracja-tabeli"
description: "Jak zbudować nową wersję tabeli obok starej, przenieść dane i kontrolowanie przełączyć aplikację."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - parallel table
  - migracja tabeli
  - schema evolution
  - zero downtime
draft: false
---

# Parallel Table: migracja do nowej tabeli bez ryzykownej przebudowy starej

Czasami zmiana modelu jest zbyt duża, aby wykonać ją przez kilka `ALTER TABLE`. Zmieniamy:

- klucz główny,
- partycjonowanie,
- kompresję,
- typy danych,
- układ indeksów,
- sposób przechowywania historii,
- znaczenie części kolumn.

Wtedy można zbudować **nową tabelę równolegle do starej**.

Wzorzec Parallel Table wygląda następująco:

1. tworzysz tabelę V2,
2. kopiujesz dane historyczne,
3. synchronizujesz zmiany bieżące,
4. porównujesz oba modele,
5. przełączasz odczyty i zapisy,
6. zachowujesz starą tabelę przez okres bezpieczeństwa,
7. usuwasz ją po potwierdzeniu poprawności.

> Zamiast przebudowywać fundament pod działającym budynkiem, budujemy nowy fundament obok i przełączamy ruch.

## Przykład

Stara tabela:

```sql
CREATE TABLE dbo.Orders
(
    OrderId    int IDENTITY(1,1) NOT NULL,
    CustomerId int NOT NULL,
    Amount     money NOT NULL,
    CreatedAt  datetime NOT NULL,

    CONSTRAINT PK_Orders
        PRIMARY KEY (OrderId)
);
```

Nowy model ma:

- `bigint` jako identyfikator,
- `decimal` zamiast `money`,
- `datetime2`,
- jawny status,
- inny układ indeksów.

```sql
CREATE TABLE dbo.OrdersV2
(
    OrderId     bigint NOT NULL,
    CustomerId  int NOT NULL,
    Amount      decimal(19,4) NOT NULL,
    OrderStatus varchar(20) NOT NULL,
    CreatedAt   datetime2(0) NOT NULL,

    CONSTRAINT PK_OrdersV2
        PRIMARY KEY CLUSTERED (OrderId),

    CONSTRAINT CK_OrdersV2_Status
        CHECK (OrderStatus IN ('New', 'Paid', 'Cancelled'))
);
```

## Kopiowanie danych historycznych

```sql
INSERT INTO dbo.OrdersV2
(
    OrderId,
    CustomerId,
    Amount,
    OrderStatus,
    CreatedAt
)
SELECT
    CONVERT(bigint, OrderId),
    CustomerId,
    CONVERT(decimal(19,4), Amount),
    'Paid',
    CONVERT(datetime2(0), CreatedAt)
FROM dbo.Orders;
```

Na dużej tabeli należy użyć migracji partiami i zapisywać postęp.

## Synchronizacja zmian

Najtrudniejsze pytanie brzmi: co z rekordami zmienianymi podczas kopiowania?

Możliwe strategie:

### Krótkie okno tylko do odczytu

Najprostsze rozwiązanie. Zatrzymujemy zapisy, kopiujemy ostatnią deltę i przełączamy tabelę. Sprawdza się, gdy akceptowalne jest krótkie okno serwisowe.

### Dual Write

Aplikacja zapisuje do obu tabel. Wymaga atomowości i monitoringu zgodności.

### Change Data Capture

Kopiujemy bazowy zestaw danych, a następnie odtwarzamy zmiany z CDC.

### Trigger synchronizujący

Trigger zapisuje zmiany do V2. Jest prosty koncepcyjnie, ale zwiększa koszt każdej operacji i ukrywa logikę.

### Kolejka zmian

Operacje trafiają do tabeli kolejki, a osobny proces aplikuje je do nowego modelu.

Wybór zależy od wymagań dotyczących przestoju, skali i tolerancji chwilowej niespójności.

## Walidacja

Porównanie liczby wierszy jest potrzebne, ale niewystarczające.

```sql
SELECT
    OldCount = (SELECT COUNT_BIG(*) FROM dbo.Orders),
    NewCount = (SELECT COUNT_BIG(*) FROM dbo.OrdersV2);
```

Warto porównać również:

```sql
SELECT
    OldAmount = SUM(CONVERT(decimal(38,4), Amount))
FROM dbo.Orders;

SELECT
    NewAmount = SUM(CONVERT(decimal(38,4), Amount))
FROM dbo.OrdersV2;
```

Dodatkowo:

- brakujące klucze,
- duplikaty,
- wartości po konwersji,
- rozkład statusów,
- zakres dat,
- losowe próbki rekordów,
- wyniki najważniejszych zapytań biznesowych.

## Przełączenie

Przełączenie może odbyć się na poziomie:

- konfiguracji aplikacji,
- procedur składowanych,
- synonimu,
- widoku,
- zmiany nazw tabel.

Przykład z synonimem:

```sql
CREATE SYNONYM app.Orders
FOR dbo.OrdersV2;
```

Synonim upraszcza zmianę obiektu docelowego, ale nie obsługuje wszystkich scenariuszy i wymaga ostrożności przy zależnościach schematu.

Zmiana nazw tabel jest efektowna, ale bywa ryzykowna. Nie aktualizuje wszystkich odwołań i może powodować chwilowe błędy pomiędzy operacjami.

## Tożsamość i nowe rekordy

Jeżeli obie tabele generują identyfikatory, łatwo o kolizję. Lepszym podejściem jest:

- generowanie klucza w jednym miejscu,
- przekazywanie identyfikatora do obu tabel,
- użycie sekwencji,
- zarezerwowanie zakresów,
- przełączenie generatora przed rozpoczęciem zapisu do V2.

Przykład sekwencji:

```sql
CREATE SEQUENCE dbo.OrderIdSequence
    AS bigint
    START WITH 1000000
    INCREMENT BY 1;
```

## Powrót do starej tabeli

Po przełączeniu nie należy natychmiast usuwać V1. Może służyć jako punkt odniesienia i opcja awaryjna.

Trzeba jednak ustalić:

- czy V1 nadal otrzymuje zapisy,
- jak długo ją przechowujemy,
- czy rollback jest możliwy po zapisaniu danych dostępnych tylko w V2,
- kiedy tabela stanie się archiwum tylko do odczytu.

## Kiedy używać?

Parallel Table jest dobrym wyborem, gdy:

- zmiana struktury jest duża,
- potrzebujemy nowych indeksów lub partycjonowania,
- konwersja in-place jest ryzykowna,
- chcemy łatwo porównywać V1 i V2,
- mamy miejsce na równoległe dane.

## Koszty

Największy koszt to przestrzeń dyskowa i synchronizacja. Przez pewien czas przechowujemy dwa pełne zestawy danych. Dodatkowo musimy rozwiązać kwestie:

- bieżących zmian,
- kluczy,
- ograniczeń,
- procedur,
- uprawnień,
- statystyk i indeksów,
- backupu i HA.

## Podsumowanie

Parallel Table jest silnym wzorcem, ponieważ daje wyraźną granicę pomiędzy starym i nowym modelem. Możemy zbudować V2, przetestować ją na rzeczywistych danych i przełączyć ruch dopiero wtedy, gdy jesteśmy gotowi.

Nie jest to jednak zwykłe `INSERT ... SELECT`. Sukces zależy od:

- synchronizacji delty,
- walidacji biznesowej,
- kontrolowanego przełączenia,
- planu rollback lub roll forward,
- zakończenia okresu równoległego.

Nowa tabela obok starej może być bezpieczniejsza niż przebudowa starej w miejscu — pod warunkiem, że dokładnie zaplanujemy moment, w którym obie wersje przestaną żyć równolegle.
