---
title: "Backup VLDB >4TB – jak nie wpaść w pułapkę"
date: 2025-10-18
slug: backup-vldb
tags: [SQLServer, Backup, Restore, HighAvailability, DBA]
draft: false
---

Przy małej bazie backup to prosty przycisk.  
Przy bazie 4 TB i więcej — to strategia.  

SQL Server potrafi wykonać kopię dowolnej wielkości bazy, ale granicą staje się infrastruktura: I/O, sieć, tempdb, a czasem… ludzkie złudzenie, że „backup się zrobi”.  

W świecie VLDB (Very Large Database) backup nie jest operacją — to **proces logistyczny**.  
Wymaga planowania, testów, segmentacji i chłodnej kalkulacji: *ile danych, w jakim czasie, dokąd i po co.*

## 1. Striped backup – nie luksus, konieczność

Backup 4 TB w jednym pliku to proszenie się o kłopoty.  
Podziel go na kilka pasków (stripes), najlepiej na osobnych wolumenach:

```sql
BACKUP DATABASE ERPCS_PROD
TO
    DISK = 'X:\Backups\ERPCS_PROD_1.bak',
    DISK = 'Y:\Backups\ERPCS_PROD_2.bak',
    DISK = 'Z:\Backups\ERPCS_PROD_3.bak',
    DISK = 'W:\Backups\ERPCS_PROD_4.bak'
WITH
    COMPRESSION,
    CHECKSUM,
    STATS = 5,
    MAXTRANSFERSIZE = 4194304,
    BUFFERCOUNT = 384;
```

Striping równoważy obciążenie i pozwala SQL Serverowi pisać równolegle.  
To często różnica między 6 godzinami a 50 minutami.

## 2. Filegroup backup – kopia tego, co naprawdę się zmienia

W VLDB pełna kopia codziennie to absurd.  
Jeśli Twoja baza ma logiczną strukturę (np. dane archiwalne, raportowe, bieżące), zrób **partial backup** lub **filegroup backup**.  

```sql
BACKUP DATABASE ERP_DB FILEGROUP = 'FG_ACTIVE' 
TO DISK = 'X:\Backups\ERP_DB_FG_ACTIVE.bak' 
WITH COMPRESSION, CHECKSUM;
```

To pozwala robić szybkie kopie aktywnych sekcji bazy i oszczędza terabajty przestrzeni.

## 3. Test restore – najczęściej pomijany punkt

Backup, którego nigdy nie odtworzyłeś, to tylko ładny plik binarny.  
Odtwarzanie VLDB to inna liga: potrzebujesz miejsca, czasu, procedur i **planów równoległych**.  

Zrób test:  
- odtwórz backup na innej instancji,  
- zmień ścieżki plików,  
- zmierz czas i zapisz wynik.  

Dopiero wtedy możesz powiedzieć: *“mam kopię zapasową.”*

## 4. Backup DIFF + LOG – najlepszy kompromis

Pełna kopia raz w tygodniu, różnicowa codziennie, log co godzinę (lub częściej).  
Dla VLDB to złoty środek między bezpieczeństwem a wydajnością.  

Pamiętaj, że backup **dziennika transakcji (LOG)** nie jest opcjonalny — to Twoja jedyna droga do punktu w czasie (*point-in-time recovery*).

## 5. Kompresja i deduplikacja – mniej znaczy więcej

SQL Server Compression potrafi zmniejszyć rozmiar backupu nawet o 70%.  
Przy backupie 24 TB to różnica między 24 TB a 7 TB – i godzinami transferu.  

W połączeniu z systemami backupowymi (Veeam, Commvault, Rubrik) z deduplikacją efekt bywa spektakularny.

## 6. Retencja i rotacja – nie wszystko trzeba trzymać wiecznie

Przy VLDB łatwo przekroczyć setki terabajtów archiwów.  
Ustal twardą politykę retencji (np. 14 dni online, 30 offline, 1 rok archiwum WORM).  
Automatyzuj czyszczenie starych kopii:

```sql
EXECUTE dbo.usp_CleanupOldBackups 
    @Path = 'X:\Backups\', 
    @RetentionDays = 14;
```

To proste, a ratuje przestrzeń i porządek.

## 7. Monitorowanie i alerty

Każdy backup musi mieć wynik i czas.  
Włącz `msdb.dbo.backupset` w monitoringu (np. Telegraf + InfluxDB + Grafana).  
Alertuj, jeśli backup trwa dłużej niż zwykle lub nie pojawił się nowy rekord.

## 8. Psychologia backupu

Najwięksi DBA przegrywali nie przez błędy w T-SQL, ale przez złudzenie bezpieczeństwa.  
Backup daje spokój tylko wtedy, gdy jest **sprawdzony, powtarzalny i mierzalny**.

> “Nie masz kopii zapasowej, dopóki jej nie odtworzyłeś.”  
> — stara prawda, która nie traci ważności, gdy baza rośnie szybciej niż Twoja macierz.

## 9. Przykładowe skrypty i konfiguracje

W moim repozytorium znajdziesz gotowe materiały do wdrożenia strategii backupu VLDB w środowisku SQL Server 2022:  
- **Skrypty T-SQL** dla striped/full/diff/log backupów,  
- **PowerShell** do automatyzacji i rotacji kopii,  
- **Telegraf + InfluxDB** dashboard do monitorowania czasu i rozmiaru backupów,  
- **Checklistę test restore**.  

🔗 [SQLManiak – Backup & Restore Scripts (GitHub)](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/06-internals/Lab07_Backup_Restore_Perf)

---

Jeśli backup trwa godziny — to nie problem.  
Problem zaczyna się wtedy, gdy nie wiesz, **ile czasu zajmie odtworzenie**.  
