---
title: "SQL Server 2025 – Nowa era pracy z danymi"
date: 2025-11-19
tags:
  - SQL Server
  - SQL Server 2025
  - Performance
  - Monitoring
  - Security
  - Query Store
  - JSON
categories:
  - SQLManiak
draft: false
---

SQL Server 2025 (17.x) wprowadza istotne zmiany dla administratorów, architektów i deweloperów. Najciekawsze dotyczą przetwarzania zapytań, nowych typów danych, integracji AI oraz zarządzania obciążeniem. Warto jednak oddzielać funkcje dostępne produkcyjnie od tych, które wymagają włączenia **PREVIEW_FEATURES**.

Poniższy przegląd opiera się na oficjalnej dokumentacji Microsoftu, a nie na marketingowych nazwach, które nie występują w specyfikacji produktu.

## Intelligent Query Processing i Query Store

SQL Server 2025 rozwija istniejącą rodzinę **Intelligent Query Processing (IQP)**. Wśród udokumentowanych zmian znajdują się:

- **Optional Parameter Plan Optimization (OPPO)** — wykorzystuje mechanizm Multiplan, aby przygotowywać warianty planu dla zapytań z opcjonalnymi predykatami.
- **Cardinality Estimation Feedback for Expressions** — pozwala silnikowi uczyć się doboru modeli estymacji dla wyrażeń.
- **Degree of Parallelism (DOP) Feedback** — jest domyślnie włączony.
- **Query Store na czytelnych replikach wtórnych** — jest domyślnie włączony w obsługiwanych konfiguracjach.
- **ABORT_QUERY_EXECUTION** — hint pozwalający blokować przyszłe wykonania wskazanych problematycznych zapytań.

Nie jest to osobny produkt o nazwie „Query Store 3.0”. W diagnostyce nadal należy analizować plany, wait statistics, Query Store i rzeczywiste zachowanie aplikacji.

## Natywny typ JSON

SQL Server 2025 udostępnia natywny typ **`json`**, przechowujący dane w zoptymalizowanym formacie binarnym. Rozszerza to możliwości pracy z dokumentami JSON w silniku relacyjnym.

Nie należy nazywać go **`JSONB`** — to nazwa kojarzona przede wszystkim z PostgreSQL, a nie typ danych SQL Server.

Dostępne są także m.in. funkcje agregujące **`JSON_OBJECTAGG`** i **`JSON_ARRAYAGG`**. Przed migracją warto sprawdzić ograniczenia, zgodność narzędzi oraz zachowanie indeksów i zapytań dla konkretnego scenariusza.

## Typ VECTOR i funkcje AI

Nowy typ **`vector`** umożliwia przechowywanie reprezentacji wektorowych używanych np. w wyszukiwaniu podobieństwa.

SQL Server 2025 udostępnia funkcje takie jak **`VECTOR_DISTANCE`**, **`VECTOR_NORM`** i **`VECTOR_NORMALIZE`**, a także mechanizmy integracji z zewnętrznymi modelami AI.

**Ważne:** przybliżone indeksowanie wektorowe i niektóre funkcje wyszukiwania wektorowego są oznaczone jako Preview i wymagają odpowiedniej konfiguracji **`PREVIEW_FEATURES`**. Funkcji Preview nie należy automatycznie traktować jako gotowych do produkcji.

## Wyrażenia regularne i funkcje T-SQL

Do języka T-SQL dodano obsługę wyrażeń regularnych, m.in.:

- **`REGEXP_LIKE`** — sprawdzenie dopasowania wzorca;
- **`REGEXP_REPLACE`** — zamiana fragmentów tekstu;
- **`REGEXP_SUBSTR`** — wyodrębnianie dopasowanego fragmentu;
- **`REGEXP_COUNT`** — zliczanie dopasowań.

Nowe możliwości upraszczają część operacji walidacji i transformacji tekstu, ale ich wpływ na wydajność trzeba mierzyć w rzeczywistym obciążeniu.

## Optimized Locking i TempDB

**Optimized Locking** ogranicza zużycie pamięci na blokady oraz może redukować blokowanie i eskalację blokad. W praktyce należy sprawdzić wymagania funkcji, edycję produktu i konfigurację bazy.

SQL Server 2025 wprowadza również **TempDB Space Resource Governance**, pomagające ograniczać skutki nadmiernego zużycia przestrzeni TempDB przez obciążenia, oraz **Accelerated Database Recovery w TempDB**.

Nie oznacza to jednak całkowitego wyeliminowania `PAGELATCH` ani uniwersalnej poprawy wydajności o określony procent.

## Columnstore, analityka i integracje

Wśród zmian dotyczących columnstore znajdują się m.in. **uporządkowane nieklastrowane indeksy columnstore** i usprawnienia ich budowania.

SQL Server 2025 rozwija również integrację z ekosystemem Microsoft Fabric i narzędziami do pracy z danymi. Zakres dostępności funkcji zależy od edycji, konfiguracji i etapu wydania.

## Bezpieczeństwo i wdrażanie

Przy planowaniu migracji warto zweryfikować zmiany dotyczące bezpieczeństwa, protokołów komunikacyjnych, uprawnień i zależności aplikacji na podstawie dokumentacji konkretnego wydania.

Nie należy zakładać istnienia osobnych mechanizmów „Security Shield” lub „Secure Credential Vault” bez potwierdzenia w dokumentacji Microsoftu.

Podobnie nie należy przyjmować, że SQL Server 2025 zapewnia oficjalne natywne obrazy kontenerowe ARM64 albo klastrowanie Availability Groups bez klastra, wyłącznie na podstawie ogólnych zapowiedzi.

## Co sprawdzić przed wdrożeniem?

1. **Kompatybilność aplikacji i sterowników** — także zachowanie nowych typów danych.
2. **Query Store i plan regression** — porównanie bazowych metryk przed i po migracji.
3. **Funkcje Preview** — czy są włączone i czy wolno ich używać w danym środowisku.
4. **Dostępność funkcji w edycji** — Enterprise, Standard i Express różnią się możliwościami.
5. **Testy backup/restore, HA/DR i wydajności** — nowa wersja silnika nie zastępuje testów operacyjnych.

## Podsumowanie

SQL Server 2025 przynosi rzeczywiste nowości: natywny `json`, typ `vector`, funkcje regex, usprawnienia IQP, Optimized Locking i nowe mechanizmy ochrony TempDB.

Najważniejsza zasada DBA pozostaje bez zmian: **najpierw potwierdź funkcję w dokumentacji, następnie przetestuj ją na swoim obciążeniu**.

Źródła:

- [What's New in SQL Server 2025 — Microsoft Learn](https://learn.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-2025?view=sql-server-ver17)
- [SQL Server 2025 Release Notes — Microsoft Learn](https://learn.microsoft.com/en-us/sql/sql-server/sql-server-2025-release-notes?view=sql-server-ver17)
- [Editions and Supported Features — Microsoft Learn](https://learn.microsoft.com/en-us/sql/sql-server/editions-and-components-of-sql-server-2025?view=sql-server-ver17)
