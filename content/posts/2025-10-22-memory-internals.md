---
title: "Wewnętrzne mechanizmy pamięci SQL Server"
date: 2025-10-22
slug: memory-internals
tags: [SQLServer, Internals, Memory, Performance, DBA]
draft: false
---

Za każdą operacją stoi pamięć: Buffer Pool, Memory Clerks, Lazy Writer i PLE (Page Life Expectancy).  
To serce SQL Servera – a każdy spadek PLE to zawał.  
Zrozumienie, jak SQL zarządza stronami danych, to klucz do prawdziwego tuningu.

> „Co nie zmieści się w pamięci, wróci po zemstę z dysku.”

Przygotowałem diagram, który pokazuje pełen przepływ stron w Buffer Pool.
