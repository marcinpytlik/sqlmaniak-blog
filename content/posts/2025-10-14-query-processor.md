---
title: "Co widzi Query Processor zanim Ty klikniesz Execute?"
date: 2025-10-14
slug: query-processor
tags: [SQLServer, TSQL, DBA, SQLQuiz, DataPlatform]
draft: false
---

Kiedy wpisujesz `SELECT` i wciskasz „Execute” — zaczyna się coś magicznego. Ale nie w takiej kolejności, jak myślisz.  
SQL Server wcale nie zaczyna od `SELECT`, tylko od `FROM`. Najpierw zbiera dane, potem filtruje, grupuje, sortuje i dopiero na końcu wybiera kolumny.  
To ma znaczenie — bo pokazuje, że to, co widzimy w kodzie, nie jest tym, co widzi Query Processor.

> “The illusion that code runs as written is one of the oldest tricks in computing.”

Zrozumienie kolejności przetwarzania to pierwszy krok, by pisać wydajnie, a nie tylko poprawnie.
