---
title: "DELETE vs TRUNCATE – kiedy SQL Server naprawdę sprząta"
date: 2025-10-15
slug: delete-vs-truncate
tags: [SQLServer, TSQL, Performance, Internals, DBA]
draft: false
---

Oba polecenia usuwają dane. Ale jedno robi to z manierą, drugie z miotłą.  
`DELETE` loguje każdy wiersz osobno — wolniej, ale precyzyjnie.  
`TRUNCATE` kasuje całe strony danych jednym ruchem, nie zapisując każdego wiersza w logu.  

Konsekwencje? Mniej logu, ale zero triggerów, brak `WHERE`, i natychmiastowy reset `IDENTITY`.  

> SQL Server pamięta więcej, niż się wydaje. Nawet po TRUNCATE — w logu transakcyjnym zostaje ślad.

W następnej „perełce z piwnicy SQL-owej” zajrzymy do ghost records.
