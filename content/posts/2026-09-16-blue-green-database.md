---
title: "Blue-Green Database Deployment: dlaczego baza jest trudniejsza niż aplikacja"
date: 2026-09-16T00:01:00+02:00
slug: "blue-green-database-deployment"
description: "Jak zastosować ideę blue-green do wdrożeń baz danych i gdzie kończy się prosta analogia z aplikacją."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - blue green deployment
  - deployment
  - zero downtime
  - database DevOps
draft: false
---

# Blue-Green Database Deployment: dlaczego baza jest trudniejsza niż aplikacja

Wdrożenie blue-green dla aplikacji jest intuicyjne:

- środowisko Blue obsługuje ruch,
- środowisko Green otrzymuje nową wersję,
- wykonujemy testy,
- przełączamy ruch,
- w razie problemu wracamy do Blue.

Baza danych jest trudniejsza, ponieważ zawiera **zmieniający się stan**.

Gdy po przełączeniu użytkownicy zapiszą nowe dane do Green, Blue nie jest już automatycznie aktualną kopią. Powrót nie polega wyłącznie na zmianie adresu endpointu.

> Blue-Green dla bazy danych nie jest problemem kopiowania schematu. Jest problemem własności i synchronizacji stanu.

## Co może oznaczać blue-green w bazie?

Termin bywa używany dla różnych rozwiązań:

1. dwie pełne bazy danych,
2. dwa schematy w jednej bazie,
3. dwie wersje tabel,
4. jedna baza zgodna jednocześnie z aplikacją Blue i Green,
5. replika przygotowana do przejęcia roli.

Każdy wariant ma inne właściwości.

## Najbezpieczniejszy wariant: jedna baza, kompatybilny schemat

Często najlepszą strategią jest nie duplikować bazy. Zamiast tego przygotowujemy schemat kompatybilny z dwiema wersjami aplikacji.

Kolejność:

1. wdrożenie rozszerzających zmian bazy,
2. uruchomienie aplikacji Green,
3. testy Green na tej samej bazie,
4. przełączenie ruchu,
5. obserwacja,
6. usunięcie starego schematu w późniejszym wdrożeniu.

To w praktyce połączenie blue-green aplikacji z wzorcem Expand–Contract dla bazy.

## Dwie pełne bazy

Załóżmy, że mamy:

```text
Sales_Blue
Sales_Green
```

Kopiujemy dane do Green, wdrażamy nowy schemat i przełączamy aplikację.

Problem: co z zapisami wykonanymi po rozpoczęciu kopiowania?

Potrzebujemy synchronizacji:

- replikacja,
- CDC,
- backup i restore plus delta,
- log shipping,
- mechanizm aplikacyjny,
- kolejka zdarzeń.

Jeżeli synchronizacja działa tylko w jedną stronę, powrót po przełączeniu może być trudny.

## Dwukierunkowa synchronizacja

Brzmi jak rozwiązanie rollbacku, ale wprowadza konflikty:

- ten sam rekord zmieniony w obu bazach,
- różna kolejność operacji,
- różne reguły walidacji,
- nowe pola istniejące tylko w Green,
- usunięcia i ponowne utworzenia,
- kolizje kluczy.

Dwukierunkowa synchronizacja często jest bardziej złożona niż sama migracja. Dlatego należy unikać sytuacji, w której oba środowiska przyjmują niezależne zapisy.

## Punkt bez powrotu

Każde wdrożenie powinno określić **point of no return**.

Przed nim możemy wrócić do Blue bez utraty danych. Po nim rollback wymaga:

- migracji danych wstecz,
- transformacji nowych wartości,
- odtworzenia zmian,
- zaakceptowania utraty części funkcjonalności.

Przykład: Green zapisuje kilka adresów klienta, a Blue obsługuje tylko jeden. Powrót wymaga decyzji, który adres zachować. Nie jest to już techniczne przełączenie.

## Przełączanie połączenia

Aplikacja może korzystać z:

- aliasu DNS,
- konfiguracji połączenia,
- sekretu,
- listenera,
- warstwy proxy.

Zmiana endpointu powinna uwzględniać pule połączeń. Stare połączenia mogą pozostać aktywne jeszcze przez pewien czas.

Należy zaplanować:

- zamknięcie lub odświeżenie connection pool,
- zachowanie transakcji w toku,
- ponawianie operacji,
- idempotencję zapisów,
- monitoring połączeń do Blue i Green.

## Testy Green

Testy na kopii danych są wartościowe, ale testy zapisujące mogą zmienić dane. Potrzebujemy:

- izolowanych kont testowych,
- oznaczonych rekordów,
- transakcji wycofywanych,
- kopii tylko do testów,
- syntetycznych scenariuszy,
- kontroli skutków procesów asynchronicznych.

Nie należy wysyłać rzeczywistych wiadomości, faktur czy powiadomień podczas testowania Green.

## Schematy Blue i Green w jednej bazie

Można utworzyć:

```text
blue.Orders
green.Orders
```

To upraszcza część synchronizacji i backupu, ale obie wersje nadal dzielą:

- zasoby instancji,
- log transakcyjny,
- awarie bazy,
- ustawienia,
- część zabezpieczeń.

Nie jest to pełna izolacja środowisk. Może jednak być użytecznym wzorcem dla tabel lub modułów, które chcemy przełączyć niezależnie.

## Obserwowalność

Po przełączeniu trzeba mierzyć:

- liczbę połączeń do obu środowisk,
- błędy aplikacji,
- czas odpowiedzi,
- blokady i deadlocki,
- wzrost logu,
- opóźnienie synchronizacji,
- różnice liczby rekordów,
- nieprzetworzone komunikaty,
- zapytania korzystające ze starego schematu.

Rollback nie powinien być decyzją opartą na ogólnym wrażeniu. Musi mieć konkretne progi.

## Kiedy blue-green ma sens?

- aplikacja może być przełączana niezależnie,
- schemat pozostaje kompatybilny,
- potrzebujemy szybkiego powrotu kodu,
- synchronizacja danych jest dobrze zdefiniowana,
- punkt bez powrotu jest świadomie zaplanowany.

## Kiedy jest zbyt kosztowny?

- baza jest bardzo duża,
- zapis jest intensywny,
- brak mechanizmu synchronizacji delty,
- nowy model nie jest kompatybilny wstecz,
- wymagany jest dwukierunkowy zapis,
- zespół nie ma narzędzi do walidacji stanu.

## Podsumowanie

Blue-Green Database Deployment nie jest prostą kopią wzorca aplikacyjnego.

Najczęściej bezpieczne podejście wygląda tak:

- aplikacje Blue i Green,
- jedna współdzielona baza,
- rozszerzający schemat zgodny z obiema wersjami,
- późniejszy etap Contract.

Dwie pełne bazy mogą być właściwe, ale wymagają odpowiedzi na pytania o synchronizację, konflikty i powrót danych.

Najważniejsza lekcja:

> Kod można przełączyć w sekundę. Stan danych trzeba przeprowadzić przez zmianę świadomie.
