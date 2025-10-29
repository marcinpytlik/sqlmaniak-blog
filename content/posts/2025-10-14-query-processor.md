---
title: "Co widzi Query Processor zanim Ty klikniesz Execute?"
date: 2025-10-14
slug: query-processor
tags: [SQLServer, TSQL, DBA, SQLQuiz, DataPlatform]
draft: false
---

Kiedy wpisujesz `SELECT` i wciskasz **„Execute”**, zaczyna się coś magicznego. Ale nie w takiej kolejności, jak myślisz.  

SQL Server nie jest naiwnym tłumaczem Twojego kodu – to **kompilator logiki zapytań**, który widzi świat zupełnie inaczej. Zanim linijka `SELECT` dotrze do procesora zapytań, tekst T-SQL zostaje **zanalizowany, przepisany, znormalizowany i zoptymalizowany**. Efektem nie jest „wykonanie kodu”, ale **plan zapytania** – precyzyjna instrukcja dla silnika relacyjnego, jak dobrać dane możliwie najtaniej.

I właśnie tu pojawia się pierwszy paradoks: SQL Server wcale nie zaczyna od `SELECT`.  
Najpierw patrzy na `FROM` – **ustala źródła danych**, sprawdza połączenia (`JOIN`), a następnie przechodzi przez kolejne etapy:

1. `FROM` + `JOIN` – ustala, skąd pobrać dane i jak je połączyć.  
2. `WHERE` – filtruje dane, zanim cokolwiek dalej pójdzie w obieg.  
3. `GROUP BY` i funkcje agregujące – buduje podsumowania.  
4. `HAVING` – filtruje wyniki grup.  
5. `SELECT` – dopiero teraz wybiera kolumny i wyrażenia.  
6. `ORDER BY` – sortuje gotowy zestaw danych.  

To nie przypadek, że wydajność często zależy od tego, **gdzie** w tym łańcuchu zrobisz selekcję, a nie od tego, **jak** ładnie napiszesz kod.

> “The illusion that code runs as written is one of the oldest tricks in computing.”

Ta iluzja działa również w SQL – składnia wygląda sekwencyjnie, ale procesor zapytań myśli algebraicznie.  
To właśnie dlatego zmiana jednego `WHERE` na `JOIN` potrafi zmienić plan wykonania o rząd wielkości.  
Zrozumienie tej logiki to pierwszy krok, by pisać **wydajnie, a nie tylko poprawnie**.

---

### Jak to sprawdzić w praktyce

Spróbuj sam.  
Uruchom w SSMS lub Azure Data Studio poniższe zapytanie:

```sql
USE AdventureWorks2022;
SET SHOWPLAN_XML ON;

SELECT p.Name, SUM(sod.LineTotal) AS Total
FROM Sales.SalesOrderDetail sod
JOIN Production.Product p ON sod.ProductID = p.ProductID
WHERE p.Color = 'Red'
GROUP BY p.Name
HAVING SUM(sod.LineTotal) > 10000
ORDER BY Total DESC;
```

SQL Server **nie wykona** zapytania – zamiast tego wygeneruje plan w formacie XML.  
Otwórz go i zobacz, że **pierwszy krok to nie SELECT**, tylko **SCAN lub SEEK** z tabeli w sekcji `RelOp LogicalOp="Clustered Index Scan"` lub `Index Seek`.  
Potem przychodzą operatory `Nested Loops`, `Hash Match`, `Filter`… wszystko w odwrotnej kolejności do tego, jak napisałeś kod.  

Wyłącz plan poleceniem:

```sql
SET SHOWPLAN_XML OFF;
```

Chcesz to zobaczyć graficznie? Użyj `Ctrl+M` przed uruchomieniem zapytania.  
Plan graficzny w SSMS pokaże, że **SELECT** siedzi na górze drzewa, ale wszystko zaczyna się na dole – od dostępu do danych.

---

Widzisz? To nie magia, tylko **algebra relacyjna w akcji**.  
Każdy `SELECT` to układanka operatorów, które Query Processor układa od dołu, a my – jako ludzie – od góry.  
Zrozumienie tej różnicy to moment, w którym przestajesz pisać zapytania, a zaczynasz je **projektować**.
