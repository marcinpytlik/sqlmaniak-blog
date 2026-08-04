---
title: "Backfill in Batches: jak migrować miliony rekordów bez jednej wielkiej transakcji"
slug: "backfill-in-batches-sql-server"
description: "Praktyczne podejście do uzupełniania nowych kolumn i migracji danych partiami w SQL Server."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - backfill
  - migracja danych
  - log transakcyjny
  - blokady
status: "draft"
---

# Backfill in Batches: jak migrować miliony rekordów bez jednej wielkiej transakcji

Dodanie nowej kolumny jest często dopiero początkiem zmiany schematu. Trzeba jeszcze uzupełnić jej wartość dla danych historycznych.

Najprostsze rozwiązanie:

```sql
UPDATE dbo.Orders
SET OrderSource = 'Legacy'
WHERE OrderSource IS NULL;
```

Na tabeli zawierającej kilka tysięcy rekordów może działać dobrze. Na tabeli liczącej setki milionów wierszy może spowodować:

- gwałtowny wzrost logu transakcyjnego,
- długie blokady,
- eskalację blokad,
- opóźnienie replikacji lub grupy dostępności,
- duży rollback po przerwaniu,
- wpływ na backupy i okna utrzymaniowe.

Wzorzec **Backfill in Batches** dzieli pracę na małe, powtarzalne transakcje.

> Celem nie jest wykonanie migracji możliwie najszybciej. Celem jest wykonanie jej w tempie, które system produkcyjny potrafi bezpiecznie obsłużyć.

## Model przykładowy

```sql
CREATE TABLE dbo.Orders
(
    OrderId     bigint IDENTITY(1,1) NOT NULL,
    CustomerId  int NOT NULL,
    CreatedAt   datetime2(0) NOT NULL,
    OrderSource varchar(30) NULL,

    CONSTRAINT PK_Orders
        PRIMARY KEY (OrderId)
);
```

Nowa kolumna `OrderSource` została dodana jako `NULL`, aby nie wymuszać natychmiastowego przepisania całej tabeli.

## Najprostsza pętla

```sql
WHILE 1 = 1
BEGIN
    UPDATE TOP (5000) dbo.Orders
    SET OrderSource = 'Legacy'
    WHERE OrderSource IS NULL;

    IF @@ROWCOUNT = 0
        BREAK;
END;
```

To już lepsze niż jedna wielka transakcja, ale nadal nie jest idealne. Każda partia może ponownie skanować dużą część tabeli.

## Migracja po kluczu

Lepszy wariant przechowuje ostatni przetworzony klucz:

```sql
DECLARE
    @BatchSize   int = 5000,
    @LastOrderId bigint = 0,
    @MaxOrderId  bigint;

SELECT @MaxOrderId = MAX(OrderId)
FROM dbo.Orders;

WHILE @LastOrderId < @MaxOrderId
BEGIN
    UPDATE dbo.Orders
    SET OrderSource = 'Legacy'
    WHERE OrderId > @LastOrderId
      AND OrderId <= @LastOrderId + @BatchSize
      AND OrderSource IS NULL;

    SET @LastOrderId += @BatchSize;
END;
```

Ten wariant jest przewidywalny, ale zakłada względnie ciągły klucz. Przy dużych lukach lepiej pobierać faktyczne identyfikatory partii.

```sql
DECLARE @BatchSize int = 5000;

WHILE 1 = 1
BEGIN
    CREATE TABLE #Batch
    (
        OrderId bigint NOT NULL PRIMARY KEY
    );

    INSERT INTO #Batch(OrderId)
    SELECT TOP (@BatchSize)
        o.OrderId
    FROM dbo.Orders AS o WITH (READPAST)
    WHERE o.OrderSource IS NULL
    ORDER BY o.OrderId;

    IF @@ROWCOUNT = 0
        BREAK;

    UPDATE o
    SET OrderSource = 'Legacy'
    FROM dbo.Orders AS o
    JOIN #Batch AS b
        ON b.OrderId = o.OrderId;

    DROP TABLE #Batch;
END;
```

## Wznawialność

Proces może zostać przerwany przez restart, wdrożenie lub okno serwisowe. Dlatego powinien umieć wznowić pracę.

Przydatna jest tabela sterująca:

```sql
CREATE TABLE dbo.DataMigrationState
(
    MigrationName   sysname NOT NULL,
    LastProcessedId bigint NOT NULL,
    RowsProcessed   bigint NOT NULL,
    LastBatchAt     datetime2(0) NULL,
    CompletedAt     datetime2(0) NULL,

    CONSTRAINT PK_DataMigrationState
        PRIMARY KEY (MigrationName)
);
```

Po każdej partii aktualizujemy stan. Dzięki temu wiemy:

- gdzie proces się zatrzymał,
- ile rekordów przetworzono,
- kiedy zakończyła się ostatnia partia,
- czy migracja została ukończona.

## Rozmiar partii

Nie istnieje jedna poprawna wartość. Partia `100`, `5000` lub `50000` może być właściwa zależnie od:

- szerokości wiersza,
- liczby indeksów,
- rodzaju aktualizacji,
- wydajności storage,
- obciążenia systemu,
- przepustowości logu,
- replikacji i HA.

Dobrym podejściem jest rozpoczęcie od małej partii i obserwacja:

- czasu partii,
- liczby logowanych bajtów,
- blokad,
- opóźnienia replik,
- użycia CPU i I/O.

## Sterowanie tempem

Można dodać przerwę:

```sql
WAITFOR DELAY '00:00:00.250';
```

Można również zatrzymywać migrację, gdy system jest obciążony lub gdy opóźnienie repliki przekroczy ustalony próg. W praktyce mechanizm sterowania powinien być prosty i przewidywalny.

## Indeks pomocniczy

Zapytanie:

```sql
WHERE OrderSource IS NULL
```

może wymagać pełnego skanu. Tymczasowy indeks filtrowany może znacząco przyspieszyć migrację:

```sql
CREATE INDEX IX_Orders_Backfill_OrderSource
ON dbo.Orders(OrderId)
WHERE OrderSource IS NULL;
```

Po zakończeniu migracji indeks można usunąć:

```sql
DROP INDEX IX_Orders_Backfill_OrderSource
ON dbo.Orders;
```

Trzeba jednak uwzględnić koszt utworzenia indeksu oraz dodatkowy koszt zapisów podczas migracji.

## Współbieżność z aplikacją

Jeżeli aplikacja zapisuje nowe rekordy, powinna od razu uzupełniać nową kolumnę. W przeciwnym razie backfill będzie stale gonił nowe wartości `NULL`.

Typowa kolejność:

1. dodaj kolumnę jako `NULL`,
2. wdroż aplikację zapisującą nową wartość,
3. uruchom backfill historycznych rekordów,
4. sprawdź brak `NULL`,
5. ustaw `NOT NULL`.

## Walidacja

Po migracji nie wystarczy komunikat „job zakończył się sukcesem”.

```sql
SELECT COUNT_BIG(*) AS MissingRows
FROM dbo.Orders
WHERE OrderSource IS NULL;
```

Wynik powinien wynosić zero.

Warto również porównać agregaty, sumy kontrolne albo wartości wyliczane ze starego i nowego modelu.

## Co z rollbackiem?

Każda partia jest osobną transakcją, więc rollback dotyczy tylko bieżącej partii. Zakończonych partii nie cofamy automatycznie.

Dlatego przed migracją należy określić, czy:

- nową wartość można ponownie wyliczyć,
- potrzebujemy tabeli zmian,
- migracja jest odwracalna,
- w przypadku błędu poprawiamy dane do przodu.

## Kiedy stosować?

Backfill w partiach jest właściwy, gdy:

- tabela jest duża,
- system musi pozostać dostępny,
- aktualizacja wpływa na log i blokady,
- migracja może trwać wiele godzin lub dni,
- proces musi być wznawialny.

## Kiedy jedna transakcja może być lepsza?

Na małej tabeli prosty `UPDATE` bywa czytelniejszy i bezpieczniejszy. Nie należy komplikować migracji bez potrzeby. Najpierw trzeba znać rozmiar danych i koszt operacji.

## Podsumowanie

Backfill in Batches jest wzorcem operacyjnym. Samo zapytanie `UPDATE` nie jest najtrudniejszą częścią. Najtrudniejsze jest kontrolowanie wpływu na działający system.

Dobra migracja partiami jest:

- wznawialna,
- idempotentna,
- monitorowana,
- walidowana,
- dostosowana do obciążenia,
- zakończona usunięciem mechanizmów tymczasowych.

Miliony rekordów nie muszą oznaczać wielkiej transakcji. Mogą oznaczać tysiące małych, przewidywalnych kroków.
