---
title: "Resource Governor – ogranicz CPU, nie ludzi"
date: 2025-10-21
slug: resource-governor
tags: [SQLServer, Performance, ResourceGovernor, TSQL, DBA]
draft: false
---

# Resource Governor – ogranicz CPU, nie ludzi

Nie każdy proces zasługuje na 100% CPU.  
Nie każdy użytkownik powinien mieć wolną autostradę do rdzeni.  
Resource Governor to strażnik równowagi – ustawia granice, zanim chaos stanie się faktem.

SQL Server potrafi być aż zbyt uprzejmy.  
Jeśli aplikacja klienta zacznie mielić raporty z JOIN-ami jak spaghetti, serwer grzecznie rzuci w to wszystkie swoje wątki – a reszta użytkowników zostaje w korku.  
Resource Governor mówi: *dość*.  

To nie kara, to **sprawiedliwość obliczeniowa**.  

Dzięki niemu możesz podzielić zasoby (CPU, pamięć, I/O) między różne **workload groups** i przypisywać do nich sesje według własnych reguł.  
To trochę jak organizacja biura open space: każda aplikacja ma swój stolik, swoje krzesło i przydział kawy.

---

## ⚙️ Jak to działa

1. **Resource Pools** – określają maksymalną (i minimalną) część CPU oraz pamięci, jaką można przydzielić.  
   Przykład: `PoolReporty` dostaje 30% CPU i 20% pamięci.

2. **Workload Groups** – to grupy sesji przypisane do konkretnych pooli.  
   Raporty, OLTP, testy – każdy ma swoje miejsce.

3. **Classifier Function** – serce mechanizmu. Funkcja T-SQL, która rozpoznaje kto się łączy i decyduje, do której grupy trafi.

---

## 🧠 Przykład konfiguracji

```sql
-- 1. Włącz Resource Governor
ALTER RESOURCE GOVERNOR RECONFIGURE;

-- 2. Utwórz Resource Pool
CREATE RESOURCE POOL PoolReporty
WITH (MAX_CPU_PERCENT = 30, MAX_MEMORY_PERCENT = 20);

-- 3. Utwórz Workload Group
CREATE WORKLOAD GROUP GrupaReporty
USING PoolReporty;

-- 4. Funkcja klasyfikująca
CREATE FUNCTION dbo.fnClassifier()
RETURNS sysname
WITH SCHEMABINDING
AS
BEGIN
    DECLARE @Group sysname;
    IF ORIGINAL_LOGIN() LIKE 'report%'
        SET @Group = 'GrupaReporty';
    ELSE
        SET @Group = 'default';
    RETURN @Group;
END;
GO

-- 5. Przypisz funkcję
ALTER RESOURCE GOVERNOR
WITH (CLASSIFIER_FUNCTION = dbo.fnClassifier);

ALTER RESOURCE GOVERNOR RECONFIGURE;
```

Teraz użytkownicy raportowi dostają swój skrawek CPU, a serwer może oddychać.

---

## 🔬 Weryfikacja

Zajrzyj do DMV:

```sql
SELECT pool_id, name, min_cpu_percent, max_cpu_percent
FROM sys.resource_governor_resource_pools;

SELECT group_id, name, pool_id
FROM sys.resource_governor_workload_groups;
```

Możesz też podejrzeć statystyki wykonania przez `sys.dm_resource_governor_workload_groups` – zobaczysz tam, kto najbardziej obciąża system.

---

## 🧩 Refleksja SQLManiaka

W świecie procesów każdy chce być królem CPU.  
Ale prawdziwa równowaga nie polega na sile – tylko na **świadomym podziale**.  
Resource Governor to narzędzie filozofa-DBA:  
uczy, że ograniczenia bywają warunkiem harmonii.  

> „Nie każda aplikacja jest równa – ale każda zasługuje na swoje 30% CPU.”
