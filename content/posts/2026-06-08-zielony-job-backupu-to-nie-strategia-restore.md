---
title: "SQL Server Backup: zielony job to jeszcze nie strategia odtwarzania"
date: 2026-06-08T20:30:00+02:00
slug: sql-server-backup-zielony-job-to-nie-strategia-restore
description: "Zielony status joba backupu w SQL Server Agent to dopiero początek. Prawdziwa strategia zaczyna się wtedy, gdy umiemy odtworzyć bazę do właściwego punktu w czasie i w akceptowalnym czasie."
tags: [SQLServer, Backup, Restore, DBA, DisasterRecovery]
categories: [SQL Server]
draft: false
---

Wracam do bloga od tematu, który w SQL Server bardzo często wygląda prosto tylko na pierwszy rzut oka.

Backup.

W wielu środowiskach pytanie o bezpieczeństwo danych kończy się na jednym zdaniu:

> Job backupu świeci się na zielono.

To dobrze. Ale to jeszcze nie oznacza, że firma ma realną strategię odtwarzania.

![SQL Server Backup i Restore — Pakiet DBA](/images/sql-server-backup-restore-pakiet-dba-cover.png)

## Zielony job to tylko informacja o wykonaniu operacji

Zielony status joba SQL Server Agent oznacza, że konkretna operacja zakończyła się sukcesem. To ważna informacja, ale bardzo ograniczona.

Nie mówi nam jeszcze, czy:

- plik backupu nadal istnieje,
- plik jest dostępny z serwera, na którym będziemy wykonywać restore,
- backup obejmuje właściwą bazę,
- mamy kompletny łańcuch backupów LOG,
- mamy certyfikat TDE i klucz prywatny,
- backup da się odtworzyć,
- czas restore mieści się w wymaganym RTO,
- biznes akceptuje możliwą utratę danych zgodnie z RPO.

Dlatego samo monitorowanie statusu joba to za mało.

## Backup nie jest celem

Backup jest tylko środkiem do celu. Celem jest skuteczne odtworzenie danych po awarii, błędzie użytkownika, uszkodzeniu bazy, utracie serwera albo incydencie bezpieczeństwa.

To jest różnica między podejściem:

```text
Czy backup się wykonał?
```

a podejściem:

```text
Czy potrafię odtworzyć bazę do właściwego punktu w czasie i w akceptowalnym czasie?
```

Pierwsze pytanie dotyczy operacji technicznej. Drugie dotyczy odpowiedzialności DBA.

## RPO i RTO muszą być punktem startowym

Strategia backupu powinna wynikać z dwóch wartości:

- **RPO** — ile danych organizacja może maksymalnie stracić,
- **RTO** — jak szybko system musi wrócić po awarii.

Jeżeli firma akceptuje utratę maksymalnie 15 minut danych, backup LOG raz na dobę nie rozwiązuje problemu. Jeżeli system musi wrócić w godzinę, a pełny restore trwa sześć godzin, sama obecność backupu nie spełnia wymagania biznesowego.

Tu zaczyna się prawdziwa rozmowa o strategii.

## Log chain — cichy bohater odtwarzania

W środowiskach pracujących w trybie `FULL` lub `BULK_LOGGED` kluczowe znaczenie ma łańcuch backupów LOG.

To dzięki niemu można odtwarzać bazę do konkretnego punktu w czasie.

Przykład:

```text
20:00 FULL backup
22:00 DIFF backup
22:15 LOG backup
22:30 LOG backup
22:45 LOG backup
23:00 LOG backup
```

Jeżeli potrzebujemy odtworzyć bazę na 22:37, sam FULL i DIFF nie wystarczą. Potrzebny jest właściwy fragment log chain oraz restore z opcją `STOPAT`.

I tu pojawia się problem: wiele osób sprawdza, czy job backupu LOG się wykonał, ale nie sprawdza ciągłości łańcucha.

Prosty przykład kontroli historii backupów LOG:

```sql
DECLARE @DatabaseName sysname = N'ERP';

WITH LogBackups AS
(
    SELECT
        bs.database_name,
        bs.backup_start_date,
        bs.backup_finish_date,
        bs.first_lsn,
        bs.last_lsn,
        LAG(bs.last_lsn) OVER
        (
            PARTITION BY bs.database_name
            ORDER BY bs.backup_start_date
        ) AS previous_last_lsn
    FROM msdb.dbo.backupset AS bs
    WHERE bs.database_name = @DatabaseName
      AND bs.type = 'L'
)
SELECT
    database_name,
    backup_start_date,
    backup_finish_date,
    previous_last_lsn,
    first_lsn,
    last_lsn,
    CASE
        WHEN previous_last_lsn IS NULL THEN 'PIERWSZY LOG W WYNIKU'
        WHEN previous_last_lsn = first_lsn THEN 'OK - CIAGLOSC'
        ELSE 'UWAGA - PRZERWA W LANCUCHU'
    END AS log_chain_status
FROM LogBackups
ORDER BY backup_start_date;
```

To nie zastępuje pełnej procedury restore, ale pozwala szybko zobaczyć, czy mamy potencjalny problem.

## TDE: backup bazy to czasem za mało

Jeżeli baza używa TDE, backup samej bazy nie wystarczy do spokojnego snu.

Potrzebne są również:

- certyfikat TDE,
- klucz prywatny,
- hasło do backupu certyfikatu,
- bezpieczne miejsce przechowywania tych elementów,
- przetestowana procedura restore na innej instancji.

Brak certyfikatu TDE może oznaczać, że backup istnieje, ale nie da się go odtworzyć tam, gdzie jest potrzebny.

To jest jeden z tych tematów, które wychodzą dopiero podczas awarii albo testu DR.

Lepiej, żeby wyszły podczas testu.

## RESTORE VERIFYONLY to nie test restore

`RESTORE VERIFYONLY` jest przydatne, ale nie jest pełnym testem odtworzenia.

Może potwierdzić, że backup wygląda na możliwy do odczytania, ale nie odpowiada na wszystkie pytania:

- czy baza się odtworzy do końca,
- czy ścieżki plików są poprawne,
- czy mamy wszystkie pliki striped backupu,
- czy certyfikaty TDE są dostępne,
- czy aplikacja ruszy po restore,
- czy po restore `DBCC CHECKDB` przejdzie poprawnie,
- ile realnie trwa cała procedura.

Prawdziwy test backupu to test restore.

## Minimalna checklista DBA

Jeżeli chcesz szybko ocenić, czy backup w środowisku SQL Server jest tylko operacją, czy już elementem strategii, zacznij od pytań:

- Czy znamy RPO i RTO dla każdej ważnej bazy?
- Czy wiemy, które bazy są w trybie `SIMPLE`, `FULL` i `BULK_LOGGED`?
- Czy backupy LOG są wykonywane z częstotliwością wynikającą z RPO?
- Czy sprawdzamy ciągłość log chain?
- Czy test restore jest wykonywany cyklicznie?
- Czy mierzymy czas restore, a nie tylko czas backupu?
- Czy backupy baz systemowych są wykonywane po zmianach konfiguracji?
- Czy mamy backup certyfikatów TDE?
- Czy mamy procedurę awaryjną dla utraty serwera lub storage?
- Czy ktoś poza jedną osobą zna procedurę odtworzeniową?

Jeżeli na większość tych pytań odpowiedź brzmi „nie wiem”, to backup może działać, ale strategia wymaga dopracowania.

## Dlaczego o tym piszę

Przez lata widziałem środowiska, w których backupy formalnie istniały. Joby były zielone, pliki się tworzyły, monitoring nie krzyczał.

Problem pojawiał się dopiero wtedy, gdy trzeba było coś odtworzyć.

Brakowało jednego pliku. Brakowało logów. Certyfikat TDE był tylko na starym serwerze. Nikt nie wiedział, który DIFF jest właściwy. Restore trwał znacznie dłużej niż zakładano. Aplikacja po restore nie działała, bo część danych była poza SQL Serverem.

Dlatego lubię powtarzać:

> Nie chodzi o to, czy backup się wykonał.  
> Chodzi o to, czy restore się uda.

## Materiał dodatkowy

Na bazie tych doświadczeń przygotowałem praktyczny pakiet DBA:

**SQL Server Backup i Restore — Pakiet DBA**

W pakiecie są:

- e-book PDF,
- skrypty T-SQL i PowerShell,
- checklisty DBA,
- runbooki restore,
- procedury awaryjne,
- materiały dotyczące RPO, RTO, LSN, log chain, TDE, gMSA, monitoringu backupów i testów restore.

Link do pakietu:

[SQL Server Backup i Restore — Pakiet DBA](https://pytlik.gumroad.com/l/sql-server-backup-restore-pakiet-dba)

To nie jest materiał o tym, jak kliknąć „Backup”.  
To materiał o tym, jak myśleć o odtwarzaniu danych w realnym środowisku SQL Server.

---

Jeżeli masz dziś w środowisku tylko zielone joby backupu, zadaj sobie jedno pytanie:

**kiedy ostatni raz naprawdę odtworzyłeś bazę z backupu?**
