---
title: "Feature Flag dla zmian schematu: kontrolowane przełączanie nowego modelu danych"
slug: "feature-flag-schema-change"
description: "Jak używać flag funkcjonalnych podczas migracji schematu i stopniowo przełączać odczyty oraz zapisy."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - feature flags
  - schema evolution
  - deployment
  - migracja danych
status: "draft"
---

# Feature Flag dla zmian schematu: kontrolowane przełączanie nowego modelu danych

Zmiana schematu i wdrożenie funkcjonalności nie muszą nastąpić w tym samym momencie.

Możemy najpierw dodać nową tabelę, wdrożyć kod, a dopiero później włączyć korzystanie z nowego modelu dla części ruchu. Pomagają w tym **Feature Flags**.

Flaga może sterować:

- odczytem ze starego lub nowego modelu,
- zapisem do jednej albo dwóch struktur,
- włączeniem nowej funkcji dla wybranych użytkowników,
- stopniowym zwiększaniem udziału ruchu,
- szybkim wyłączeniem nowej ścieżki bez ponownego wdrożenia kodu.

> Feature Flag oddziela moment wdrożenia kodu od momentu aktywacji nowego zachowania.

## Przykładowy scenariusz

Aplikacja migruje z kolumny `Customers.AddressText` do tabeli `CustomerAddresses`.

Możemy zdefiniować trzy flagi:

```text
UseNewAddressRead
UseNewAddressWrite
EnableAddressV2
```

Każda steruje innym etapem.

## Nie jedna flaga, lecz osobne decyzje

Jedna flaga `NewAddressModel` może być zbyt ogólna. Odczyt i zapis mają inne ryzyka.

Lepsza kolejność:

1. nowy zapis jest wykonywany w tle,
2. odczyt nadal korzysta ze starego modelu,
3. porównujemy wyniki obu odczytów,
4. przełączamy niewielką część użytkowników,
5. zwiększamy udział,
6. wyłączamy stary zapis,
7. usuwamy flagi po zakończeniu migracji.

## Gdzie przechowywać flagi?

Możliwe miejsca:

- system zarządzania flagami,
- konfiguracja aplikacji,
- tabela w bazie,
- zmienne środowiskowe.

Prosta tabela:

```sql
CREATE TABLE config.FeatureFlags
(
    FeatureName  sysname NOT NULL,
    IsEnabled    bit NOT NULL,
    Percentage   tinyint NULL,
    UpdatedAt    datetime2(0) NOT NULL,
    UpdatedBy    sysname NOT NULL,

    CONSTRAINT PK_FeatureFlags
        PRIMARY KEY (FeatureName),

    CONSTRAINT CK_FeatureFlags_Percentage
        CHECK (Percentage BETWEEN 0 AND 100)
);
```

Aplikacja nie powinna odpytywać tej tabeli przed każdą operacją bez cache. Trzeba również uwzględnić opóźnienie propagacji zmiany.

## Flaga odczytu

Kod może wybrać źródło danych:

```text
if UseNewAddressRead:
    read CustomerAddresses
else:
    read Customers.AddressText
```

Lepszy wariant w okresie testowym to **shadow read**:

1. wynik dla użytkownika pochodzi ze starego modelu,
2. aplikacja odczytuje również nowy model,
3. porównuje wyniki,
4. zapisuje różnice do telemetryki.

Użytkownik nie odczuwa zmiany, a zespół zbiera dowody zgodności.

## Flaga zapisu

Możliwe tryby:

```text
LegacyOnly
DualWrite
NewOnly
```

To czytelniejsze niż kilka niezależnych wartości logicznych, które mogą utworzyć niedozwoloną kombinację.

W bazie można przechowywać stan:

```sql
CREATE TABLE config.AddressWriteMode
(
    Mode varchar(20) NOT NULL,

    CONSTRAINT CK_AddressWriteMode
        CHECK (Mode IN ('LegacyOnly', 'DualWrite', 'NewOnly'))
);
```

Najważniejsze jest zapewnienie, że zmiana trybu nie nastąpi w połowie transakcji i że wszystkie instancje aplikacji interpretują ją w ten sam sposób.

## Stopniowe wdrożenie

Nowy model można włączyć dla:

- pracowników,
- tenantów testowych,
- konkretnego regionu,
- wybranych klientów,
- określonego procentu ruchu.

Przypisanie musi być stabilne. Ten sam klient nie powinien losowo przełączać się pomiędzy V1 i V2 przy każdym żądaniu.

Można użyć funkcji skrótu identyfikatora:

```text
hash(CustomerId) % 100 < Percentage
```

Dzięki temu grupa użytkowników pozostaje stała przy danym procencie.

## Baza nadal musi być kompatybilna

Feature Flag nie zastępuje poprawnego projektu schematu.

Jeżeli wyłączenie flagi ma przywrócić starą ścieżkę, stary model musi nadal zawierać dane potrzebne do działania. Po zapisaniu informacji dostępnych tylko w V2 cofnięcie flagi może być niemożliwe.

Flaga daje możliwość wyłączenia kodu, ale nie cofa automatycznie danych.

## Monitorowanie

Każda aktywacja powinna być powiązana z metrykami:

- liczba operacji V1 i V2,
- błędy dla każdej ścieżki,
- różnice wyników shadow read,
- czas odpowiedzi,
- liczba niespójnych rekordów,
- deadlocki i blokady,
- kolejka oczekujących migracji,
- użycie starego modelu.

Przykładowa tabela rozbieżności:

```sql
CREATE TABLE audit.AddressReadDifferences
(
    DifferenceId bigint IDENTITY(1,1) NOT NULL,
    CustomerId   int NOT NULL,
    LegacyValue  nvarchar(500) NULL,
    NewValue     nvarchar(500) NULL,
    DetectedAt   datetime2(0) NOT NULL,

    CONSTRAINT PK_AddressReadDifferences
        PRIMARY KEY (DifferenceId)
);
```

## Awaryjne wyłączenie

Flaga powinna umożliwiać szybkie zatrzymanie nowej ścieżki. Trzeba jednak wiedzieć, co dokładnie oznacza wyłączenie:

- tylko odczyty wracają do V1,
- zapisy nadal trafiają do V2,
- oba kierunki zostają zatrzymane,
- wymagane jest opróżnienie kolejki,
- dane V2 trzeba zsynchronizować wstecz.

Bez tej definicji „kill switch” może stworzyć większą niespójność.

## Dług techniczny flag

Flagi przejściowe należy usuwać.

Każda pozostawiona flaga:

- zwiększa liczbę ścieżek kodu,
- komplikuje testy,
- utrudnia analizę błędów,
- może prowadzić do kombinacji, których nikt nie przewidział.

Dobrą praktyką jest zapisanie dla flagi:

- właściciela,
- celu,
- daty utworzenia,
- warunku usunięcia,
- maksymalnego czasu życia.

## Kiedy stosować?

Feature Flag jest dobrym rozwiązaniem, gdy:

- chcemy stopniowo zwiększać ruch,
- nowy kod można wdrożyć nieaktywny,
- potrzebujemy szybkiego wyłączenia funkcji,
- chcemy wykonać shadow read,
- migracja obejmuje wiele instancji aplikacji.

## Kiedy uważać?

- stary model nie potrafi reprezentować nowych danych,
- zapis jest rozproszony pomiędzy systemami,
- flagi nie są spójnie propagowane,
- nie ma monitoringu porównawczego,
- zespół nie usuwa flag po migracji.

## Podsumowanie

Feature Flag pozwala kontrolować tempo przejścia na nowy schemat. Nie zmienia jednak podstawowych zasad:

- schemat musi być kompatybilny,
- dane muszą być migrowane,
- zapisy muszą być spójne,
- wyniki muszą być porównywane,
- stary model trzeba ostatecznie usunąć.

Flaga nie jest planem migracji. Jest narzędziem, które pozwala ten plan wykonać stopniowo i bez ponownego wdrażania aplikacji.
