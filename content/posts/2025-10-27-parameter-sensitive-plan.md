---
title: "Parameter Sensitive Plan – inteligencja kontekstowa SQL Servera"
date: 2025-10-27
slug: parameter-sensitive-plan
tags: [SQLServer, PSP, Performance, QueryOptimization, Internals]
draft: false
---

Każdy plan zapytania to decyzja, **jak przejść od danych do wyniku**.  
Przez lata SQL Server zapamiętywał **pierwszy** plan (parameter sniffing) i używał go zawsze, nawet gdy kolejne parametry miały inny rozkład danych.

## 💡 Co wnosi PSP (SQL Server 2022)?
Mechanizm **Parameter Sensitive Plan (PSP)** pozwala **utrzymywać kilka wariantów planu** dla **tego samego zapytania**, zoptymalizowanych pod różne „konteksty parametrów”.  
Przy każdym wywołaniu optymalizator używa **dispatcher’a**, który dobiera najlepszy wariant do bieżących wartości.

- 1 `query_id` → wiele `plan_id`
- Query Store zapisuje warianty (łatwo je analizować)
- Runtime wybiera plan na podstawie „bucketów” selektywności
📂 Repo: [PSP](https://github.com/marcinpytlik/SQLManiak/tree/master/sqlmaniak_blog/PSP-DEMO)

## ⚙️ Jak uruchomić demo
1. Otwórz repo w VS Code
2. Ustaw zmienne środowiskowe:
   ```powershell
   $env:MSSQL_SERVER="localhost"
   $env:MSSQL_USER="sa"
   $env:MSSQL_PASS="YourStrong!Passw0rd"
   ```
3. Uruchom taski: **00 → 03**, potem **04 – Compare IO/CPU** lub zapytania z folderu `sql/dmv`.

## 🔬 Co zobaczysz
- **≥2 warianty planu** w Query Store dla `dbo.GetOrdersByCustomer`
- W XML planu: `<ParameterSensitivePlan>True</ParameterSensitivePlan>`
- Różnice w IO/CPU pomiędzy parametrami „rzadkimi” i „gorącymi”

## 🧩 Dobre praktyki
- **Query Store w READ_WRITE** – PSP korzysta z QS
- Unikaj mieszania z hintami `OPTIMIZE FOR`
- PSP dotyczy planów parametryzowanych (procedury / sp_executesql)

> „Inteligencja to zdolność adaptacji do zmian.” — *Stephen Hawking*
