---
title: "Jak udowodnić, że starego schematu nikt już nie używa"
date: 2026-12-09T00:01:00+01:00
slug: "deprecacja-starego-schematu"
description: "Praktyczne podejście do deprecacji starej tabeli, kolumny lub widoku przed etapem Contract."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - schema evolution
  - deprecation
  - Extended Events
  - database DevOps
draft: false
---

# Jak udowodnić, że starego schematu nikt już nie używa

Najbardziej ryzykowny moment migracji nie zawsze jest na początku.

Często jest nim usunięcie starego obiektu.

## „Aplikacja już nie używa” to za mało

Ze starego schematu mogą korzystać:

- raporty,
- ETL,
- ręczne skrypty,
- integracje,
- narzędzia BI,
- joby SQL Agent,
- starsze wersje aplikacji.

## Zależności statyczne

```sql
SELECT
    OBJECT_SCHEMA_NAME(referencing_id) AS SchemaName,
    OBJECT_NAME(referencing_id) AS ObjectName,
    referenced_entity_name
FROM sys.sql_expression_dependencies
WHERE referenced_entity_name = N'LegacyOrders';
```

To dobry początek, ale nie wykryje dynamicznego SQL i zapytań spoza bazy.

## Telemetria rzeczywistego użycia

Extended Events może pomóc zarejestrować zapytania zawierające nazwę starego obiektu.

Przykładowa idea filtra:

```text
sql_text LIKE '%LegacyOrders%'
```

Nie jest to idealny parser zależności, ale pozwala zebrać dowody z produkcyjnego ruchu.

## Okres deprecacji

Dobrze mieć jawny okres:

1. obiekt oznaczony jako legacy,
2. monitoring użycia,
3. kontakt z właścicielami konsumentów,
4. data wyłączenia,
5. etap Contract.

## Rename jako alarm?

Czasem w kontrolowanym oknie można zmienić nazwę obiektu lub odebrać dostęp, żeby ujawnić ukrytych konsumentów.

To ryzykowna technika i wymaga planu szybkiego cofnięcia.

## Podsumowanie

Nie usuwaj starego schematu dlatego, że wydaje Ci się nieużywany.

Usuń go wtedy, gdy masz obserwowalne dowody, że przestał być częścią systemu.