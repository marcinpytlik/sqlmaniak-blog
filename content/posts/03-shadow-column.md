---
title: "Shadow Column: bezpieczna zmiana typu kolumny w SQL Server"
slug: "shadow-column-zmiana-typu-kolumny"
description: "Jak zmienić typ lub znaczenie kolumny bez ryzykownego ALTER COLUMN na dużej tabeli."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - shadow column
  - ALTER TABLE
  - migracja danych
  - zero downtime
status: "draft"
---

# Shadow Column: bezpieczna zmiana typu kolumny w SQL Server

Zmiana typu kolumny wygląda na prostą operację:

```sql
ALTER TABLE dbo.Documents
ALTER COLUMN DocumentNumber varchar(30) NOT NULL;
```

Na małej tabeli może zakończyć się szybko. Na dużej tabeli produkcyjnej może jednak oznaczać:

- długą blokadę modyfikacji schematu,
- przebudowę danych,
- wzrost logu transakcyjnego,
- przebudowę indeksów,
- konflikt z aktywnymi zapytaniami,
- problem z aplikacją oczekującą starego typu.

Wzorzec **Shadow Column** pozwala przeprowadzić zmianę etapami. Zamiast modyfikować istniejącą kolumnę, dodajemy nową kolumnę obok niej.

> Shadow Column zamienia jedną dużą zmianę w kilka małych, kontrolowanych kroków.

## Scenariusz

Pierwsza wersja systemu przechowuje numer dokumentu jako `int`:

```sql
CREATE TABLE dbo.Documents
(
    DocumentId     bigint IDENTITY(1,1) NOT NULL,
    DocumentNumber int NOT NULL,

    CONSTRAINT PK_Documents
        PRIMARY KEY (DocumentId)
);
```

Po kilku latach numer dokumentu ma zawierać prefiks, na przykład `FV/2026/1001`. Typ `int` przestaje wystarczać.

## Etap 1: dodanie kolumny cienia

```sql
ALTER TABLE dbo.Documents
ADD DocumentNumberV2 varchar(30) NULL;
```

Nowa kolumna początkowo dopuszcza `NULL`. Dzięki temu jej dodanie nie wymaga natychmiastowego uzupełnienia wszystkich rekordów.

W tym momencie stara aplikacja nadal korzysta z `DocumentNumber`, a nowa może być przygotowywana do obsługi `DocumentNumberV2`.

## Etap 2: backfill

Dane historyczne przenosimy partiami:

```sql
WHILE 1 = 1
BEGIN
    UPDATE TOP (5000) dbo.Documents
    SET DocumentNumberV2 =
        CONVERT(varchar(30), DocumentNumber)
    WHERE DocumentNumberV2 IS NULL;

    IF @@ROWCOUNT = 0
        BREAK;

    WAITFOR DELAY '00:00:00.200';
END;
```

Krótka pauza pomiędzy partiami nie zawsze jest konieczna, ale może ograniczyć presję na log, I/O i blokady.

Należy monitorować:

```sql
SELECT
    TotalRows = COUNT_BIG(*),
    MigratedRows = COUNT_BIG(DocumentNumberV2),
    MissingRows = SUM(
        CASE WHEN DocumentNumberV2 IS NULL
             THEN 1 ELSE 0 END
    )
FROM dbo.Documents;
```

## Etap 3: zapis do obu kolumn

W okresie przejściowym procedura może utrzymywać obie wartości:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_Document_Create
    @DocumentNumberV2 varchar(30)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @LegacyNumber int =
        TRY_CONVERT(int, @DocumentNumberV2);

    INSERT INTO dbo.Documents
    (
        DocumentNumber,
        DocumentNumberV2
    )
    VALUES
    (
        @LegacyNumber,
        @DocumentNumberV2
    );
END;
```

Ten przykład ujawnia ważny problem: nowy format nie zawsze da się odwzorować na stary. Numer `FV/2026/1001` nie mieści się semantycznie w `int`.

Oznacza to, że pełny dual write jest możliwy tylko do momentu użycia wartości nieobsługiwanych przez stary model. Ten moment powinien być świadomym punktem przełączenia.

## Etap 4: przełączenie odczytów

Nowa wersja aplikacji zaczyna odczytywać `DocumentNumberV2`.

W okresie zgodności można zastosować:

```sql
SELECT
    DocumentId,
    EffectiveDocumentNumber =
        COALESCE(
            DocumentNumberV2,
            CONVERT(varchar(30), DocumentNumber)
        )
FROM dbo.Documents;
```

Lepszym rozwiązaniem bywa widok zgodności lub procedura, która ukrywa szczegóły migracji przed aplikacją.

## Indeksy i ograniczenia

Jeżeli stara kolumna była indeksowana, nowa zwykle również będzie wymagać indeksu:

```sql
CREATE UNIQUE INDEX UX_Documents_DocumentNumberV2
ON dbo.Documents(DocumentNumberV2)
WHERE DocumentNumberV2 IS NOT NULL;
```

Indeks filtrowany pozwala utworzyć ograniczenie przed zakończeniem migracji.

Po uzupełnieniu danych można sprawdzić duplikaty:

```sql
SELECT
    DocumentNumberV2,
    COUNT_BIG(*) AS DuplicateCount
FROM dbo.Documents
GROUP BY DocumentNumberV2
HAVING COUNT_BIG(*) > 1;
```

Dopiero gdy wynik jest pusty, możemy bezpiecznie wymusić pełną unikalność.

## Etap 5: zaostrzenie modelu

Po zakończeniu migracji:

```sql
ALTER TABLE dbo.Documents
ALTER COLUMN DocumentNumberV2 varchar(30) NOT NULL;
```

Ta operacja nadal wymaga ostrożności. Przed jej wykonaniem należy potwierdzić brak wartości `NULL` oraz ocenić blokady. W zależności od rozmiaru tabeli i wersji SQL Servera warto przeprowadzić test na kopii danych o zbliżonej skali.

## Etap 6: usunięcie starej kolumny

Po wycofaniu starej aplikacji i zależności:

```sql
ALTER TABLE dbo.Documents
DROP COLUMN DocumentNumber;
```

Następnie można zmienić nazwę nowej kolumny, ale nie zawsze jest to najlepszy krok. Zmiana nazwy ponownie modyfikuje kontrakt. Czasem bezpieczniej pozostawić nazwę `DocumentNumberV2`, a później przeprowadzić osobny etap porządkowy.

## Triggery synchronizujące

Czasami spotyka się trigger kopiujący wartości pomiędzy kolumnami. Może to być szybki mechanizm przejściowy, ale ma koszty:

- ukrywa logikę zapisu,
- komplikuje operacje wielowierszowe,
- zwiększa koszt każdej modyfikacji,
- może prowadzić do rekursji lub trudnych błędów,
- bywa pomijany podczas analizy aplikacji.

Jeżeli logikę można umieścić w jednej procedurze lub warstwie aplikacji, zwykle jest ona łatwiejsza do obserwacji.

## Kiedy wzorzec jest szczególnie przydatny?

Shadow Column sprawdza się przy:

- zmianie typu danych,
- zmianie jednostki, na przykład grosze na wartość dziesiętną,
- nowym sposobie kodowania wartości,
- podziale jednej wartości na kilka kolumn,
- wprowadzeniu szyfrowanej wersji danych,
- migracji starego identyfikatora na nowy.

## Koszty i ryzyka

Przez okres migracji tabela jest szersza, a zapis może być droższy. Trzeba również pilnować zgodności obu kolumn i zakończyć sprzątanie.

Największym błędem jest pozostawienie kolumny cienia na zawsze. Wtedy zespół przestaje wiedzieć, która wersja jest aktualna.

## Podsumowanie

`ALTER COLUMN` jest operacją techniczną. Zmiana kontraktu danych jest procesem architektonicznym.

Shadow Column daje czas na:

- przeniesienie danych,
- wdrożenie nowego kodu,
- porównanie wartości,
- przygotowanie indeksów,
- wycofanie starego modelu.

Zamiast ryzykować jedną dużą zmianę, budujemy bezpieczną ścieżkę przejścia od starego znaczenia kolumny do nowego.
