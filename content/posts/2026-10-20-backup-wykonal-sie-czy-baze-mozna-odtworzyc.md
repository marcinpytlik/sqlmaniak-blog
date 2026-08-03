---
title: "Backup się wykonał. Czy to oznacza, że bazę można odtworzyć?"
date: 2026-10-20T20:00:00+02:00
slug: backup-wykonal-sie-czy-baze-mozna-odtworzyc
description: "Dlaczego poprawny status backupu nie gwarantuje skutecznego restore. Testy odtwarzania, CHECKSUM, VERIFYONLY, TDE, RPO i RTO."
tags: [SQLServer, Backup, Restore, DisasterRecovery, DBA]
categories: [SQL Server]
draft: false
---

Zielony status joba backupowego odpowiada na jedno pytanie:

> Czy polecenie backupu zakończyło się sukcesem?

Nie odpowiada na pytanie:

> Czy potrafimy odtworzyć bazę w wymaganym czasie i do właściwego punktu?

## Backup z CHECKSUM

```sql
BACKUP DATABASE [TwojaBaza]
TO DISK = N'X:\Backup\TwojaBaza_FULL.bak'
WITH
    COMPRESSION,
    CHECKSUM,
    STATS = 10;
```

## RESTORE VERIFYONLY

```sql
RESTORE VERIFYONLY
FROM DISK = N'X:\Backup\TwojaBaza_FULL.bak'
WITH CHECKSUM;
```

Polecenie jest przydatne, ale nie potwierdza kompletności łańcucha, dostępności certyfikatu TDE, czasu restore ani działania aplikacji.

## Pełny test restore

```sql
RESTORE DATABASE [TwojaBaza_RestoreTest]
FROM DISK = N'X:\Backup\TwojaBaza_FULL.bak'
WITH
    MOVE N'TwojaBaza_Data'
        TO N'Y:\RestoreTest\TwojaBaza_RestoreTest.mdf',
    MOVE N'TwojaBaza_Log'
        TO N'Z:\RestoreTest\TwojaBaza_RestoreTest.ldf',
    RECOVERY,
    CHECKSUM,
    STATS = 10;
```

Po odtworzeniu:

```sql
DBCC CHECKDB (N'TwojaBaza_RestoreTest')
WITH NO_INFOMSGS;
```

## TDE i certyfikaty

Backup zaszyfrowanej bazy może być poprawny, ale niemożliwy do odtworzenia bez certyfikatu i klucza prywatnego.

Plan DR powinien obejmować eksport, bezpieczne przechowywanie i test importu.

## RPO i RTO

RPO określa maksymalną akceptowalną utratę danych.

RTO określa maksymalny czas przywrócenia działania.

Backup może być technicznie poprawny, ale strategia nadal może nie spełniać wymagań.

## Co mierzyć podczas testu?

- czas odnalezienia plików,
- czas kopiowania,
- czas restore,
- czas recovery,
- czas `DBCC CHECKDB`,
- czas testu aplikacji,
- całkowity czas procedury.

## Podsumowanie

Backup nie jest potwierdzeniem gotowości.

Gotowość potwierdza dopiero przetestowany restore.

Spokojny DBA regularnie udowadnia, że potrafi odtworzyć dane i zmieścić się w RPO oraz RTO.
