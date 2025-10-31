---
title: "PIOSEE: framework incydentów dla DBA + szablon do kopiuj‑wklej"
date: "2025-10-04"
slug: "piosee-framework-dla-dba"
draft: false
description: "Praktyczny szablon rozwiązywania incydentów (Problem–Information–Options–Select–Execute–Evaluate) z przykładami dla SQL Server."
tags: ["DBA", "Incydenty", "Runbook", "PIOSEE", "Productivity"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/piosee-framework-dla-dba.png"
canonical: "https://sqlmaniak.blog/piosee-framework-dla-dba"
---

Lead
----
Gdy system płonie, chcesz procedury, nie poezji. PIOSEE to sześć kroków, które trzymają nerwy na wodzy i dane przy życiu.

## Szablon
**P – Problem**: opis objawu + metryka (np. `Backup FULL > 4h`).  
**I – Information**: fakty/DMV/logi bez interpretacji.  
**O – Options**: lista możliwych rozwiązań (bez oceny).  
**S – Select**: wybór opcji (czas, ryzyko, wpływ).  
**E – Execute**: plan wykonania i komunikacja.  
**E – Evaluate**: ocena skutków, wnioski, monitoring.

## Przykład: log 95% full
- **Problem**: `% Log Used` skacze do 95% w MyDb.  
- **Information**: brak `BACKUP LOG` od 18h, `vlf_active=1` na końcu pliku.  
- **Options**: backup logu; tymczasowe powiększenie logu; kill długiej transakcji.  
- **Select**: backup logu + powiększenie do 64GB; nie zabijamy transakcji.  
- **Execute**: `BACKUP LOG`, `ALTER DATABASE ... MODIFY FILE`; notyfikacja do zespołu.  
- **Evaluate**: VLF w normie, `% Used < 30%`, alert założony.

## Gotowiec (Markdown)
```
# PIOSEE – Incydent: <tytuł>

## P – Problem
<co nie działa>

## I – Information
<logi/DMV/screeny>

## O – Options
- [ ] Opcja A
- [ ] Opcja B

## S – Select
Wybrano: <opcja>, uzasadnienie.

## E – Execute
Kroki, właściciele, okno, rollback plan.

## E – Evaluate
Wynik, metryki po, wnioski, zadania follow‑up.
```
