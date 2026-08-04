---
title: "Compatibility View: jak zmienić model i nie zepsuć starych raportów"
date: 2026-09-02T00:01:00+02:00
slug: "compatibility-view-widok-zgodnosci"
description: "Widok zgodności jako przejściowa warstwa pomiędzy starym kontraktem danych a nowym modelem SQL Server."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - widoki
  - kompatybilność
  - raporty
  - migracja schematu
draft: false
---

# Compatibility View: jak zmienić model i nie zepsuć starych raportów

Zmiana modelu danych nie kończy się na aplikacji. Z tabel korzystają również:

- raporty,
- procesy ETL,
- integracje,
- arkusze użytkowników,
- zapytania ad hoc,
- systemy, o których zespół bazodanowy może nawet nie wiedzieć.

Wzorzec **Compatibility View** polega na utworzeniu widoku, który prezentuje nowy model w formacie oczekiwanym przez starych konsumentów.

> Widok zgodności oddziela fizyczną strukturę danych od tymczasowego kontraktu, który musimy jeszcze utrzymać.

## Scenariusz

Stara tabela klientów zawierała:

```sql
dbo.Customers
(
    CustomerId,
    CustomerName,
    AddressText
)
```

Po normalizacji adresy znajdują się w tabeli `CustomerAddresses`.

Stary raport nadal wykonuje:

```sql
SELECT
    CustomerId,
    CustomerName,
    AddressText
FROM dbo.Customers;
```

Natychmiastowe usunięcie kolumny złamie raport.

## Widok zgodności

Możemy utworzyć widok odtwarzający stary format:

```sql
CREATE OR ALTER VIEW dbo.vw_Customers_Legacy
AS
    SELECT
        c.CustomerId,
        c.CustomerName,
        AddressText =
            CONCAT(
                ca.AddressLine1,
                CASE
                    WHEN ca.PostalCode IS NOT NULL
                      OR ca.City IS NOT NULL
                    THEN N', '
                    ELSE N''
                END,
                COALESCE(ca.PostalCode + N' ', N''),
                COALESCE(ca.City, N'')
            )
    FROM dbo.Customers AS c
    OUTER APPLY
    (
        SELECT TOP (1)
            a.AddressLine1,
            a.PostalCode,
            a.City
        FROM dbo.CustomerAddresses AS a
        WHERE a.CustomerId = c.CustomerId
        ORDER BY
            a.IsPrimary DESC,
            a.CustomerAddressId
    ) AS ca;
```

Raport może zostać przełączony z tabeli na widok bez znajomości nowego modelu.

## Zachowanie starej nazwy obiektu

Czasami stosuje się bardziej agresywny wariant:

1. zmiana nazwy starej tabeli,
2. utworzenie widoku pod starą nazwą,
3. nowy model znajduje się w innych tabelach.

Przykład koncepcyjny:

```sql
EXEC sys.sp_rename
    N'dbo.Customers',
    N'Customers_Internal';

CREATE VIEW dbo.Customers
AS
SELECT ...
```

To podejście może ograniczyć liczbę zmian po stronie konsumentów, ale wymaga bardzo dokładnych testów. Aplikacje mogą oczekiwać, że obiekt jest tabelą, wykonywać zapis, używać hintów albo polegać na określonych metadanych.

Zmiana nazwy przez `sp_rename` również nie aktualizuje automatycznie wszystkich odwołań tekstowych.

## Widok tylko do odczytu czy także do zapisu?

Najbezpieczniejszy Compatibility View służy do odczytu.

Widok może być aktualizowalny automatycznie tylko w prostych przypadkach. Przy złożonym mapowaniu można zastosować `INSTEAD OF TRIGGER`, ale zwiększa to ukrytą złożoność.

```sql
CREATE OR ALTER TRIGGER dbo.tr_CustomersLegacy_Update
ON dbo.vw_Customers_Legacy
INSTEAD OF UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Jawne przepisanie starego kontraktu
    -- na operacje w nowym modelu.
END;
```

Trigger musi poprawnie obsługiwać operacje wielowierszowe, błędy, transakcje i współbieżność. Dlatego taki mechanizm powinien być rozwiązaniem przejściowym, a nie trwałym API bazy.

## Stabilny kontrakt

Widok zgodności powinien dokładnie odwzorowywać:

- nazwy kolumn,
- typy danych,
- znaczenie wartości,
- obsługę `NULL`,
- liczbę wierszy,
- reguły wyboru danych.

Jeżeli nowy model przechowuje kilka adresów, a stary kontrakt jeden, trzeba ustalić, który adres zwracamy. Najczęściej będzie to adres główny, ale decyzja musi być jawna.

Bez tej reguły widok może zwracać duplikaty klientów i zmienić wyniki raportów.

## Wydajność

Widok nie przechowuje danych. Każde zapytanie wykonuje jego definicję.

Jeżeli stary raport wcześniej odczytywał jedną tabelę, a teraz widok łączy kilka dużych tabel, wydajność może się pogorszyć.

Należy sprawdzić:

- plan wykonania,
- indeksy na kluczach łączenia,
- selektywność filtrów,
- liczbę wierszy po złączeniu,
- wpływ funkcji i konwersji typów,
- zachowanie parametrów raportu.

Przykładowy indeks:

```sql
CREATE INDEX IX_CustomerAddresses_Customer_Primary
ON dbo.CustomerAddresses
(
    CustomerId,
    IsPrimary
)
INCLUDE
(
    AddressLine1,
    PostalCode,
    City
);
```

## Wersjonowanie widoków

Zamiast jednego obiektu „legacy” można jawnie wersjonować kontrakty:

```text
reporting.vw_Customers_v1
reporting.vw_Customers_v2
```

Daje to większą przejrzystość. Konsument wie, z której wersji korzysta, a zespół może zaplanować wycofanie V1.

Warto zapisać:

- właściciela każdego konsumenta,
- datę planowanego przełączenia,
- datę wyłączenia starego widoku,
- sposób monitorowania użycia.

## Jak sprawdzić, czy widok jest nadal używany?

SQL Server nie przechowuje kompletnej historii wszystkich konsumentów. Możemy jednak wykorzystać:

- Query Store,
- Extended Events,
- analizę plan cache,
- logi raportów,
- repozytoria kodu,
- audyt zapytań,
- monitoring błędów po kontrolowanym wyłączeniu w środowisku testowym.

Widok zgodności bez właściciela i daty usunięcia ma dużą szansę pozostać na zawsze.

## Kiedy używać?

Compatibility View jest dobrym rozwiązaniem, gdy:

- zmienia się fizyczny model, ale stary format odczytu jest nadal potrzebny,
- raporty migrują wolniej niż aplikacja,
- potrzebujemy kontrolowanego okresu przejściowego,
- mapowanie starego kontraktu na nowy jest jednoznaczne.

## Kiedy nie używać?

Widok może być niewłaściwy, gdy:

- wymagany jest intensywny zapis,
- mapowanie powoduje utratę znaczenia danych,
- zapytania stają się bardzo kosztowne,
- konsument polega na cechach tabeli,
- warstwa zgodności ma nieokreślony czas życia.

## Podsumowanie

Compatibility View jest skuteczną warstwą przejściową. Pozwala rozwijać model bez jednoczesnego przełączania wszystkich raportów i integracji.

Nie powinien jednak maskować problemu bez końca.

Dobry widok zgodności ma:

- jasno zdefiniowany kontrakt,
- testy wyników,
- akceptowalny plan wykonania,
- właściciela,
- monitoring użycia,
- datę wycofania.

Jego zadaniem jest kupić czas na migrację, a nie zatrzymać ewolucję schematu.
