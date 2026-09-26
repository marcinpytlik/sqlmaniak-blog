---
title: "CHECK Constraint jako etap migracji, nie jednorazowa blokada"
date: 2026-12-02T00:01:00+01:00
slug: "check-constraint-stopniowe-wdrozenie"
description: "Jak stopniowo wprowadzać nowe reguły walidacji danych za pomocą CHECK Constraint bez zaskoczenia starej aplikacji."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - CHECK constraint
  - schema evolution
  - data quality
  - deployment
draft: false
---

# CHECK Constraint jako etap migracji, nie jednorazowa blokada

Nowa reguła biznesowa często trafia do kodu aplikacji.

Ale jeśli ma obowiązywać zawsze, warto ostatecznie zapisać ją również w bazie.

## Przykład

`DiscountPercent` ma być w zakresie od 0 do 100.

```sql
SELECT *
FROM dbo.OrderDiscount
WHERE DiscountPercent < 0
   OR DiscountPercent > 100;
```

Najpierw sprawdź dane istniejące.

## Potem popraw producentów danych

Nie dodawaj constraintu, jeśli aktywna wersja aplikacji nadal zapisuje wartości, które go łamią.

Najpierw wdrażamy kod zgodny z nową regułą.

## Dodanie constraintu

```sql
ALTER TABLE dbo.OrderDiscount WITH CHECK
ADD CONSTRAINT CK_OrderDiscount_Percent
CHECK (DiscountPercent BETWEEN 0 AND 100);
```

## NULL to osobna decyzja

`CHECK (DiscountPercent BETWEEN 0 AND 100)` nie oznacza automatycznie `NOT NULL`.

Jeżeli wartość ma być obowiązkowa, potrzebny jest osobny etap.

## Monitoring przed constraintem

Przez okres przejściowy warto mierzyć liczbę rekordów naruszających przyszłą regułę.

To daje odpowiedź, czy aplikacje rzeczywiście są gotowe.

## Nie używaj constraintu jako niespodzianki produkcyjnej

Constraint powinien formalizować regułę, która już jest prawdziwa w działającym systemie.

## Podsumowanie

Najlepszy moment na dodanie constraintu jest wtedy, gdy dane i aplikacje już zachowują się tak, jakby on istniał.