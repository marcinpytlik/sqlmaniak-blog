---
title: "Ghost Records – duchy w bazie danych"
date: 2025-10-16
slug: ghost-records
tags: [SQLServer, Internals, DBCC, GhostCleanup, DBA]
draft: false
---

W bazie danych straszy.  
Nie w horrorze, ale w DMV: `sys.dm_db_index_physical_stats`.  
Gdy kasujesz wiersz, SQL Server nie usuwa go od razu — zostawia **ducha** (*ghost record*), który czeka, aż *ghost cleanup task* wykona egzorcyzm.

To dzięki temu `ROLLBACK` może przywrócić dane, a `DELETE` nie musi blokować świata.  
System woli oznaczyć rekord jako „martwy”, niż ryzykować chaos w strukturze stron danych.

> „To, czego nie widzisz, nie znaczy, że tego nie ma — zwłaszcza w bazie danych.”

---

### Jak powstaje duch

Gdy wykonujesz `DELETE`, SQL Server:
1. Zaznacza rekord jako *ghosted* (flaga w nagłówku rekordu na stronie danych).
2. Aktualizuje wskaźniki w strukturze B-tree, by rekord nie był już widoczny dla zapytań.
3. Pozostawia same dane na stronie — nadal istnieją fizycznie, ale są „niewidzialne”.

To nie błąd, lecz **mechanizm bezpieczeństwa i wydajności**.  
Dzięki niemu silnik może błyskawicznie cofnąć transakcję (`ROLLBACK`) lub, w razie potrzeby, odczytać wersję danych podczas operacji czytających.

---

### Egzorcyzm: Ghost Cleanup Task

Co pewien czas w tle działa *ghost cleanup task* — wewnętrzny proces, który przeszukuje strony z duchami i usuwa je na dobre.  
Nie dzieje się to natychmiast, bo SQL Server musi mieć pewność, że:
- żadna aktywna transakcja nie potrzebuje już tego rekordu,
- żadna sesja nie korzysta z wersji strony,
- nikt nie trzyma blokady, która uniemożliwia czyszczenie.

Zdarza się, że duchy zostają na dłużej — np. po długich transakcjach, problemach z blokadami, albo gdy baza jest w trybie **READ_COMMITTED_SNAPSHOT** i trzyma wersje w tempdb.

---

### Jak je zobaczyć

Duchów nie widać w `SELECT *`, ale można je wypatrzeć w narzędziach diagnostycznych:

```sql
DBCC CHECKTABLE ('TwojaTabela') WITH TABLERESULTS;
```

Wynik zawiera kolumnę `GhostRecCnt`, która zdradza, ile rekordów w tabeli czeka na usunięcie.  
Więcej danych znajdziesz też w DMV:

```sql
SELECT
    object_name(object_id) AS [Tabela],
    index_type_desc,
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED')
WHERE ghost_record_count > 0;
```

---

### Gdy duchy nie znikają

W rzadkich przypadkach *ghost cleanup* może nie nadążać — np. przy dużej ilości operacji `DELETE` lub błędach na poziomie stron.  
Pomaga wtedy:

```sql
DBCC FORCEGHOSTCLEANUP;
```

...czyli ręczne wezwanie pogromcy duchów.  
Ale uwaga: to operacja intensywna I/O, więc wykonuj ją rozważnie — najlepiej poza godzinami szczytu.

---

### Po co to wszystko?

Mechanizm ghost records to część **ARIES** – modelu odzyskiwania danych opartego na zasadzie *Write-Ahead Logging*.  
Zachowuje spójność, umożliwia odtwarzanie po awarii i gwarantuje, że żaden rekord nie „zniknie” zanim system upewni się, że może.

Usuwanie w SQL Server to proces, nie moment.  
Każdy `DELETE` to obietnica — że system kiedyś posprząta, gdy świat znów będzie spokojny.

---

> „Czasem to, co martwe, wciąż żyje — dopóki nie napisze się do logu transakcji, że naprawdę odeszło.”

---

### Eksperyment

Spróbuj sam:

```sql
CREATE TABLE GhostDemo(Id INT IDENTITY PRIMARY KEY, Data CHAR(200) DEFAULT 'x');
GO
INSERT INTO GhostDemo DEFAULT VALUES;
GO 1000
DELETE FROM GhostDemo WHERE Id <= 900;
GO
DBCC CHECKTABLE('GhostDemo') WITH TABLERESULTS;
```

Sprawdź kolumnę `GhostRecCnt` i zobacz, jak długo duchy utrzymują się w tabeli.  
Potem odczekaj chwilę i uruchom polecenie ponownie — egzorcyzm zadziałał.

---

Zajrzenie w świat ghost records to jak spojrzenie w **międzyczas danych** — krainę pomiędzy „było” a „nie ma”.  
SQL Server zna te granice dobrze.  
Dzięki temu nasz świat danych pozostaje uporządkowany, nawet jeśli czasem nawiedzony.
