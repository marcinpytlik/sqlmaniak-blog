---
title: "Rollback po migracji danych: kiedy cofnięcie kodu już nie wystarcza"
date: 2026-12-16T00:01:00+01:00
slug: "rollback-migracji-danych"
description: "Jak projektować rollback przy zmianach schematu, gdy nowy model danych nie jest już w pełni reprezentowalny w starym."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - rollback
  - schema evolution
  - migracja danych
  - database DevOps
draft: false
---

# Rollback po migracji danych: kiedy cofnięcie kodu już nie wystarcza

Rollback aplikacji jest łatwy tylko wtedy, gdy dane nadal pasują do starego modelu.

Po zmianie semantyki danych może pojawić się **point of no return**.

## Przykład

Stary model przechowuje jeden adres klienta.

Nowy model pozwala zapisać dowolną liczbę adresów.

Po utworzeniu trzech adresów nie istnieje automatyczna odpowiedź na pytanie, który z nich ma wrócić do starej kolumny.

## Trzy rodzaje rollbacku

### 1. Rollback kodu

Nowa wersja aplikacji zostaje wycofana, ale dane pozostają kompatybilne.

### 2. Rollback ruchu

Ruch wraca do starej ścieżki przez Feature Flag lub routing.

### 3. Rollback danych

Wymaga transformacji nowego modelu z powrotem do starego.

To najtrudniejszy wariant.

## Zdefiniuj punkt bez powrotu

Przed wdrożeniem określ zdarzenie, po którym automatyczny rollback przestaje być bezpieczny.

Może nim być:

- pierwszy zapis wartości nieobsługiwanej przez V1,
- usunięcie starej kolumny,
- migracja kluczy,
- włączenie nowego procesu biznesowego.

## Forward fix

Po punkcie bez powrotu bezpieczniejsze może być naprawienie nowej wersji niż cofanie danych.

To powinno być świadomą częścią runbooka.

## Co zapisać przed zmianą?

- sposób rollbacku kodu,
- sposób rollbacku ruchu,
- możliwość rollbacku danych,
- maksymalny czas decyzji,
- wymagane backupy i checkpointy,
- właściciela decyzji.

## Podsumowanie

Rollback nie jest jednym przyciskiem.

Im bardziej nowy model zmienia znaczenie danych, tym bardziej potrzebujesz jawnej granicy między rollbackiem a forward fix.