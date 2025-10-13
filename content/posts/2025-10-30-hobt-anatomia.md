---
title: "HOBT – hierarchia porządku danych"
date: 2025-10-30
slug: hobt-anatomia
tags: [SQLServer, Internals, Indexes, HOBT, Storage]
draft: false
---

Dane w SQL Serverze nie leżą luzem. Tworzą drzewa, a ich gałęzie prowadzą do stron danych.  
HOBT (Heap Or B-Tree) to szkielet, który utrzymuje porządek. Każdy liść ma swoje miejsce, każdy korzeń – swoją strukturę.

### 🔍 Zajrzyj w DMV
```sql
-- przeanalizuj strukturę indeksów i HOBT
SELECT OBJECT_NAME(object_id) AS TableName, index_id, index_type_desc, hobt_id
FROM sys.indexes;
```

> „Struktura jest formą istnienia porządku.” — SQLManiak
