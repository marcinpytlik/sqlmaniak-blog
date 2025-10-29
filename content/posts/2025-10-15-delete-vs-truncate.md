---
title: "DELETE vs TRUNCATE – kiedy SQL Server naprawdę sprząta"
date: 2025-10-15
slug: delete-vs-truncate
tags: [SQLServer, TSQL, Performance, Internals, DBA]
draft: false
---

Oba polecenia usuwają dane. Ale jedno robi to z manierą, drugie z miotłą.  
`DELETE` i `TRUNCATE` wyglądają podobnie — efekt końcowy to pusta tabela.  
Pod maską SQL Server jednak wykonuje zupełnie inne operacje.

### DELETE – chirurg z lupą

`DELETE` działa **wiersz po wierszu**. Każdy usunięty rekord jest logowany w transakcyjnym logu (`transaction log`), dzięki czemu można cofnąć operację (`ROLLBACK`).  
To daje precyzję — można użyć `WHERE`, aktywują się `TRIGGERY`, a relacje z kluczami obcymi są respektowane.  
Ale cena jest jasna: **log rośnie**, a wydajność spada proporcjonalnie do liczby usuwanych wierszy.

To jak sprzątanie po imprezie z pęsetą — dokładnie, ale długo.

### TRUNCATE – operator buldożera

`TRUNCATE TABLE` nie przejmuje się pojedynczymi wierszami.  
SQL Server **zwalnia całe strony danych** (8 KB każda) i odnotowuje w logu tylko deallokację tych stron, a nie każdego wiersza.  
Dlatego działa błyskawicznie i generuje **minimalny log**.

Nie można jednak dodać `WHERE`, nie zadziałają `TRIGGERY`, a `IDENTITY` wraca do wartości początkowej.  
Dodatkowo – `TRUNCATE` wymaga uprawnień `ALTER` na tabeli i nie zadziała, jeśli istnieje `FOREIGN KEY` odnoszący się do niej.

To jak spuszczenie całej wody z basenu – szybkie, ale nie da się zostawić jednej rybki.

### Log, backup i ślady po sprzątaniu

Warto wiedzieć, że nawet `TRUNCATE` **nie jest poza prawem logu**.  
Zdarzenia dealokacji stron trafiają do `transaction log` i mogą zostać odczytane narzędziami takimi jak `fn_dblog()`.  
SQL Server zawsze zostawia trop — minimalny, ale wystarczający do odtworzenia struktury transakcji.

Z punktu widzenia backupów różnica jest kolosalna:  
- `DELETE` zwiększy rozmiar logu, co wpływa na kolejne backupy logów.  
- `TRUNCATE` pozostawi log niemal nienaruszony, co przydaje się przy czyszczeniu tabel tymczasowych lub stagingowych.

> „SQL Server pamięta więcej, niż się wydaje. Nawet po TRUNCATE — w logu transakcyjnym zostaje ślad.”

### Bonus dla dociekliwych

Jeśli chcesz zobaczyć to w akcji:
```sql
CREATE TABLE Demo (ID INT IDENTITY, Data CHAR(100));
INSERT INTO Demo (Data) VALUES (REPLICATE('X', 100));
DELETE FROM Demo;
TRUNCATE TABLE Demo;
```

A potem zajrzyj do logu:
```sql
SELECT [Operation], [Context], [Page ID]
FROM fn_dblog(NULL, NULL)
WHERE [AllocUnitName] LIKE '%Demo%';
```

Zobaczysz, że `DELETE` zapisuje tysiące operacji, a `TRUNCATE` – zaledwie kilka.

---

W następnej „perełce z piwnicy SQL-owej” zajrzymy do **ghost records** — bo nawet gdy myślisz, że wiersze zniknęły, SQL Server często tylko udaje, że ich nie ma :).
