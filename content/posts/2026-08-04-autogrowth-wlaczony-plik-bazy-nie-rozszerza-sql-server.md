---
title: "Autogrowth jest włączony, a plik bazy nadal się nie rozszerza. Jak to możliwe?"
date: 2026-08-04T20:00:00+02:00
slug: autogrowth-wlaczony-plik-bazy-nie-rozszerza-sql-server
description: "Autogrowth w SQL Server nie gwarantuje, że plik bazy danych zawsze się rozszerzy. Sprawdź najczęstsze przyczyny, zapytania diagnostyczne i dobre praktyki zarządzania przestrzenią."
tags: [SQLServer, Autogrowth, MDF, NDF, LDF, DBA, Troubleshooting]
categories: [SQL Server]
draft: false
---

Jednym z częstszych nieporozumień podczas administracji SQL Server jest przekonanie, że włączenie opcji **autogrowth** rozwiązuje wszystkie problemy związane z miejscem w bazie danych.

W praktyce może się zdarzyć sytuacja, w której:

- autogrowth jest włączony,
- plik bazy danych ma ustawiony przyrost,
- baza zgłasza brak wolnego miejsca,
- aplikacja zaczyna zwracać błędy,
- a plik mimo wszystko się nie rozszerza.

Na pierwszy rzut oka wygląda to jak błąd SQL Servera.

Najczęściej jednak problem nie leży w samym mechanizmie autogrowth, ale w ograniczeniach, których SQL Server nie jest w stanie samodzielnie obejść.

W tym wpisie pokażę:

- czym naprawdę jest autogrowth,
- dlaczego plik może się nie rozszerzyć,
- jak sprawdzić wykorzystanie plików,
- jak znaleźć rzeczywistą przyczynę problemu,
- jakie ustawienia są bezpieczniejsze w środowisku produkcyjnym.

## Czym jest autogrowth?

Autogrowth to mechanizm automatycznego rozszerzania pliku bazy danych.

Gdy w pliku danych lub pliku logu zaczyna brakować wolnego miejsca, SQL Server może zwiększyć jego rozmiar zgodnie z ustawioną konfiguracją.

Przykładowo plik danych może mieć ustawiony przyrost:

```text
1024 MB
```

Oznacza to, że po wyczerpaniu wolnej przestrzeni SQL Server spróbuje powiększyć plik o 1 GB.

Nie oznacza to jednak, że rozszerzenie zawsze się powiedzie.

Autogrowth jest jedynie próbą zwiększenia pliku. SQL Server nadal potrzebuje:

- wolnego miejsca na dysku,
- uprawnień systemowych,
- możliwości zwiększenia pliku,
- poprawnej konfiguracji maksymalnego rozmiaru,
- odpowiednio wydajnego podsystemu dyskowego.

Najważniejsza zasada brzmi:

> Autogrowth nie tworzy miejsca na dysku. Wykorzystuje jedynie przestrzeń, która już istnieje.

## Wolne miejsce w pliku a wolne miejsce na dysku

To dwa całkowicie różne pojęcia.

### Wolne miejsce w pliku

Plik MDF lub NDF może mieć rozmiar 100 GB, ale tylko 80 GB może być wykorzystane przez dane.

W takim przypadku plik ma jeszcze 20 GB wolnej przestrzeni wewnętrznej.

SQL Server może zapisywać dane bez zwiększania fizycznego rozmiaru pliku.

### Wolne miejsce na dysku

Jeżeli plik ma 100 GB i jest wykorzystany niemal w całości, SQL Server będzie próbował go powiększyć.

Aby to zrobić, dysk musi posiadać odpowiednią ilość wolnego miejsca.

Jeżeli dysk jest pełny, autogrowth nie zadziała.

To właśnie ten przypadek często prowadzi do sytuacji:

```text
Free space: 0 MB
```

przy jednocześnie włączonym autogrowth.

Autogrowth jest skonfigurowany poprawnie, ale system operacyjny nie ma już przestrzeni, którą mógłby przekazać SQL Serverowi.

## Jak sprawdzić rozmiar plików bazy danych?

Podstawowe informacje o plikach można sprawdzić przy użyciu widoku `sys.database_files`:

```sql
SELECT
    name AS LogicalFileName,
    type_desc AS FileType,
    physical_name AS PhysicalFileName,
    size / 128.0 AS FileSizeMB,
    max_size,
    growth,
    is_percent_growth
FROM sys.database_files;
```

Zapytanie pokazuje:

- logiczną nazwę pliku,
- typ pliku,
- fizyczną ścieżkę,
- aktualny rozmiar,
- maksymalny rozmiar,
- wartość autogrowth,
- informację, czy wzrost jest ustawiony procentowo.

Warto zwrócić szczególną uwagę na kolumny:

```text
max_size
growth
is_percent_growth
```

## Jak odczytać konfigurację autogrowth?

Jeżeli:

```text
is_percent_growth = 0
```

to wartość `growth` jest przechowywana w stronach po 8 KB.

Aby przeliczyć ją na megabajty:

```sql
SELECT
    name,
    growth / 128.0 AS GrowthMB
FROM sys.database_files
WHERE is_percent_growth = 0;
```

Jeżeli:

```text
is_percent_growth = 1
```

to kolumna `growth` oznacza procent.

Przykładowo:

```text
growth = 10
```

oznacza wzrost o 10%.

W środowiskach produkcyjnych bezpieczniejszym rozwiązaniem jest zazwyczaj wzrost o stałą wartość, na przykład:

```text
512 MB
1024 MB
4096 MB
```

Rozszerzanie procentowe staje się nieprzewidywalne wraz ze wzrostem pliku.

Dla pliku 10 GB wzrost o 10% oznacza około 1 GB.

Dla pliku 1 TB ten sam procent oznacza już około 100 GB.

## Jak sprawdzić zajętość plików danych?

Do sprawdzenia wykorzystania plików danych można użyć funkcji `FILEPROPERTY`:

```sql
SELECT
    df.name AS LogicalFileName,
    df.type_desc AS FileType,
    df.physical_name,
    df.size / 128.0 AS FileSizeMB,
    FILEPROPERTY(df.name, 'SpaceUsed') / 128.0 AS UsedSpaceMB,
    (
        df.size -
        FILEPROPERTY(df.name, 'SpaceUsed')
    ) / 128.0 AS FreeSpaceMB,
    CAST(
        100.0 * FILEPROPERTY(df.name, 'SpaceUsed') / NULLIF(df.size, 0)
        AS decimal(10,2)
    ) AS UsedPercent
FROM sys.database_files AS df
WHERE df.type = 0;
```

Wynik pokaże:

- rozmiar pliku,
- wykorzystaną przestrzeń,
- wolną przestrzeń,
- procent zajętości.

Jeżeli `FreeSpaceMB` wynosi 0 lub jest bardzo małe, plik będzie musiał się wkrótce rozszerzyć.

To jednak nadal nie odpowiada na pytanie, czy dysk posiada wolne miejsce.

## Jak sprawdzić wolne miejsce na dysku?

Do sprawdzenia wolnego miejsca na woluminach można użyć dynamicznego widoku zarządzania:

```sql
SELECT DISTINCT
    vs.volume_mount_point,
    vs.logical_volume_name,
    vs.total_bytes / 1024.0 / 1024 / 1024 AS TotalSizeGB,
    vs.available_bytes / 1024.0 / 1024 / 1024 AS FreeSpaceGB,
    CAST(
        100.0 * vs.available_bytes / NULLIF(vs.total_bytes, 0)
        AS decimal(10,2)
    ) AS FreeSpacePercent
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats(mf.database_id, mf.file_id) AS vs
ORDER BY vs.volume_mount_point;
```

To jedno z najważniejszych zapytań podczas diagnostyki problemów z autogrowth.

Jeżeli wolne miejsce na dysku wynosi kilka megabajtów albo 0 GB, plik nie będzie mógł się rozszerzyć.

## Najczęstsze przyczyny braku rozszerzenia pliku

### 1. Brak wolnego miejsca na dysku

To najczęstsza przyczyna.

Plik może mieć autogrowth, ale dysk jest pełny.

W takim przypadku SQL Server może zgłosić błąd podobny do:

```text
Could not allocate space for object
because the filegroup is full.
```

albo:

```text
Autogrow of file failed because
there is insufficient disk space.
```

Rozwiązaniem może być:

- zwolnienie miejsca,
- przeniesienie pliku,
- rozszerzenie woluminu,
- dodanie kolejnego pliku do filegroup,
- usunięcie niepotrzebnych plików z dysku.

Nie należy jednak usuwać plików bazy danych ręcznie z poziomu systemu operacyjnego.

### 2. Ustawiony maksymalny rozmiar pliku

Plik może mieć autogrowth, ale jednocześnie posiadać ograniczenie `MAXSIZE`.

Przykład:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Data',
    MAXSIZE = 100GB
);
```

Jeżeli plik osiągnie 100 GB, nie rozszerzy się dalej.

Konfigurację można sprawdzić poleceniem:

```sql
SELECT
    name,
    size / 128.0 AS CurrentSizeMB,
    CASE
        WHEN max_size = -1 THEN 'UNLIMITED'
        ELSE CAST(max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB
FROM sys.database_files;
```

Wartość:

```text
max_size = -1
```

oznacza brak limitu na poziomie SQL Servera.

Nie oznacza to jednak braku limitu dysku.

### 3. Filegroup jest pełna

Baza może posiadać kilka filegroupów.

Tabela lub indeks mogą znajdować się w konkretnej filegroupie, która nie ma już miejsca.

Inna filegroupa może mieć wolną przestrzeń, ale SQL Server nie wykorzysta jej automatycznie dla obiektu przypisanego do innej grupy plików.

Konfigurację można sprawdzić:

```sql
SELECT
    fg.name AS FilegroupName,
    df.name AS LogicalFileName,
    df.physical_name,
    df.size / 128.0 AS FileSizeMB,
    CASE
        WHEN df.max_size = -1 THEN 'UNLIMITED'
        ELSE CAST(df.max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB
FROM sys.filegroups AS fg
INNER JOIN sys.database_files AS df
    ON fg.data_space_id = df.data_space_id
ORDER BY
    fg.name,
    df.name;
```

Jeżeli problem dotyczy filegroupy, możliwe rozwiązania to:

- zwiększenie istniejącego pliku,
- dodanie kolejnego pliku do tej samej filegroupy,
- przeniesienie obiektu,
- archiwizacja danych.

### 4. Zbyt duża wartość autogrowth

Załóżmy, że na dysku pozostało 800 MB.

Plik ma ustawiony autogrowth:

```text
1024 MB
```

SQL Server spróbuje zwiększyć plik o 1 GB.

Operacja się nie powiedzie, mimo że na dysku nadal znajduje się pewna ilość miejsca.

To ważne, ponieważ autogrowth nie musi automatycznie dopasować się do dostępnej przestrzeni.

Jeżeli skonfigurowano przyrost 4 GB, SQL Server będzie próbował przydzielić 4 GB.

W sytuacji awaryjnej można tymczasowo zmniejszyć wartość przyrostu, ale nie powinno to zastępować poprawnego zarządzania pojemnością.

### 5. Problem dotyczy pliku logu, a nie pliku danych

Plik danych i plik logu działają inaczej.

Plik logu może być duży, ale brak wolnego miejsca nie zawsze oznacza, że należy go natychmiast rozszerzać.

Najpierw należy sprawdzić, dlaczego log nie może zostać ponownie wykorzystany.

Podstawowe zapytanie:

```sql
SELECT
    name,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE name = DB_NAME();
```

Kolumna `log_reuse_wait_desc` może wskazać przyczynę, na przykład:

```text
LOG_BACKUP
ACTIVE_TRANSACTION
AVAILABILITY_REPLICA
REPLICATION
CHECKPOINT
```

W przypadku modelu FULL warto sprawdzić, czy regularnie wykonywane są kopie logu transakcyjnego.

Rozszerzenie pliku logu może usunąć objaw tylko na chwilę.

Jeżeli przyczyna nie zostanie usunięta, plik ponownie się zapełni.

### 6. Brak uprawnień konta usługi SQL Server

SQL Server działa na koncie usługi systemowej, domenowej albo gMSA.

Konto usługi musi posiadać odpowiednie uprawnienia do katalogu, w którym znajdują się pliki bazy.

Jeżeli uprawnienia zostały zmienione albo plik został przeniesiony, SQL Server może mieć problem z operacją rozszerzenia.

Taka sytuacja jest rzadsza niż brak miejsca na dysku, ale nadal możliwa.

Warto wtedy sprawdzić:

- konto usługi SQL Server,
- uprawnienia NTFS,
- dziennik błędów SQL Server,
- dziennik zdarzeń systemu Windows.

### 7. System plików lub storage posiada dodatkowe ograniczenia

W środowiskach wirtualnych i macierzowych mogą występować dodatkowe limity.

Przykładowo:

- wolumin w systemie Windows ma wolne miejsce,
- ale datastore hypervisora jest pełny,
- thin provisioning nie ma fizycznej przestrzeni,
- udział sieciowy osiągnął limit,
- storage posiada quota,
- LUN nie może zostać rozszerzony.

SQL Server widzi wyłącznie końcowy rezultat: pliku nie da się zwiększyć.

Dlatego diagnostyka czasami wymaga współpracy z administratorem systemu, wirtualizacji albo macierzy.

## Jak sprawdzić błędy autogrowth?

Informacji należy szukać przede wszystkim w SQL Server Error Log.

Można użyć:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'Autogrow';
```

Można również wyszukać błędy związane z brakiem miejsca:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'Could not allocate space';
```

oraz:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'insufficient disk space';
```

Warto również monitorować zdarzenia wzrostu plików za pomocą Extended Events.

## Czy autogrowth to mechanizm zarządzania przestrzenią?

Nie.

Autogrowth powinien być traktowany jako zabezpieczenie awaryjne, a nie podstawowy sposób zarządzania rozmiarem bazy.

Dobrą praktyką jest:

- odpowiednie wstępne rozmiarowanie plików,
- monitorowanie trendu wzrostu,
- ustawienie alertów,
- zapewnienie zapasu przestrzeni,
- ręczne zwiększanie plików przed przewidywanym wzrostem danych.

Jeżeli baza codziennie rozszerza się automatycznie, oznacza to zwykle, że zarządzanie pojemnością wymaga poprawy.

## Dlaczego częsty autogrowth jest problemem?

Każda operacja zwiększenia pliku danych może powodować opóźnienie.

W przypadku pliku danych czas operacji można znacząco ograniczyć dzięki funkcji Instant File Initialization.

Nie dotyczy ona jednak pliku logu transakcyjnego.

Rozszerzanie logu wymaga fizycznego wyzerowania nowo przydzielonej przestrzeni.

Duży autogrowth logu może więc spowodować zauważalne zatrzymanie operacji.

Z kolei bardzo mały autogrowth może prowadzić do:

- częstych operacji zwiększenia pliku,
- wielu małych fragmentów VLF w logu,
- dodatkowego narzutu,
- spadków wydajności,
- trudniejszej kontroli nad pojemnością.

Dlatego wartość przyrostu powinna być dobrana do rozmiaru i charakteru bazy.

## Przykładowa konfiguracja autogrowth

Dla pliku danych:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Data',
    FILEGROWTH = 1024MB
);
```

Dla pliku logu:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Log',
    FILEGROWTH = 512MB
);
```

Nie istnieje jedna poprawna wartość dla każdej bazy.

Konfiguracja zależy od:

- rozmiaru bazy,
- tempa wzrostu,
- obciążenia,
- czasu dopuszczalnego na operację autogrowth,
- wydajności storage,
- modelu recovery,
- częstotliwości backupów logu.

## Zbiorcze zapytanie diagnostyczne

Poniższe zapytanie pozwala szybko sprawdzić najważniejsze informacje o plikach aktualnej bazy:

```sql
SELECT
    DB_NAME() AS DatabaseName,
    df.file_id AS FileId,
    df.name AS LogicalFileName,
    df.type_desc AS FileType,
    df.physical_name AS PhysicalFileName,
    df.size / 128.0 AS FileSizeMB,
    CASE
        WHEN df.type = 0
        THEN FILEPROPERTY(df.name, 'SpaceUsed') / 128.0
        ELSE NULL
    END AS UsedSpaceMB,
    CASE
        WHEN df.type = 0
        THEN
            (
                df.size -
                FILEPROPERTY(df.name, 'SpaceUsed')
            ) / 128.0
        ELSE NULL
    END AS FreeSpaceMB,
    CASE
        WHEN df.max_size = -1
        THEN 'UNLIMITED'
        ELSE CAST(df.max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB,
    CASE
        WHEN df.is_percent_growth = 1
        THEN CAST(df.growth AS varchar(20)) + '%'
        ELSE CAST(df.growth / 128.0 AS varchar(20)) + ' MB'
    END AS Autogrowth
FROM sys.database_files AS df
ORDER BY df.file_id;
```

Dodatkowo warto połączyć wynik z informacją o wolnym miejscu na dysku:

```sql
SELECT DISTINCT
    DB_NAME(mf.database_id) AS DatabaseName,
    mf.name AS LogicalFileName,
    mf.physical_name,
    vs.volume_mount_point,
    vs.total_bytes / 1024.0 / 1024 / 1024 AS TotalSizeGB,
    vs.available_bytes / 1024.0 / 1024 / 1024 AS FreeSpaceGB,
    CAST(
        100.0 * vs.available_bytes /
        NULLIF(vs.total_bytes, 0)
        AS decimal(10,2)
    ) AS FreeSpacePercent
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats
(
    mf.database_id,
    mf.file_id
) AS vs
WHERE mf.database_id = DB_ID()
ORDER BY mf.file_id;
```

## Co zrobić, gdy plik ma 0 MB wolnego miejsca?

Najpierw należy zachować spokój i ustalić, czego dokładnie brakuje.

### Krok 1. Sprawdź typ pliku

Czy problem dotyczy:

- MDF,
- NDF,
- LDF?

Diagnostyka pliku danych różni się od diagnostyki pliku logu.

### Krok 2. Sprawdź wolne miejsce wewnątrz pliku

Dla pliku danych użyj `FILEPROPERTY`.

### Krok 3. Sprawdź wolne miejsce na dysku

Użyj `sys.dm_os_volume_stats`.

### Krok 4. Sprawdź MAXSIZE

Plik może posiadać ograniczenie maksymalnego rozmiaru.

### Krok 5. Sprawdź wartość autogrowth

Przyrost może być większy niż dostępna przestrzeń.

### Krok 6. Sprawdź SQL Server Error Log

Szukaj błędów autogrowth i alokacji.

### Krok 7. Jeżeli to log, sprawdź log_reuse_wait_desc

Nie zwiększaj pliku logu bez ustalenia przyczyny jego zapełnienia.

### Krok 8. Oceń tempo wzrostu

Jednorazowy skok może być wynikiem:

- importu,
- przebudowy indeksów,
- operacji ETL,
- dużej transakcji,
- błędu aplikacji,
- niekontrolowanego procesu archiwizacji.

## Czego nie robić?

W sytuacji braku miejsca łatwo wykonać działanie, które pogorszy problem.

Nie należy:

- usuwać plików MDF, NDF lub LDF z dysku,
- wykonywać shrink bez zrozumienia przyczyny,
- ustawiać autogrowth na bardzo małą wartość,
- ustawiać wzrostu procentowego bez analizy,
- zwiększać logu bez sprawdzenia `log_reuse_wait_desc`,
- zakładać, że `UNLIMITED` oznacza nieskończoną przestrzeń,
- ignorować powtarzających się zdarzeń autogrowth.

Szczególnie niebezpieczne jest traktowanie shrink jako standardowej metody odzyskiwania przestrzeni.

Shrink może prowadzić do fragmentacji indeksów i jest narzędziem do konkretnych, wyjątkowych scenariuszy.

## Jak zapobiegać takim problemom?

Najlepsza diagnostyka to taka, której nie trzeba wykonywać podczas awarii.

Warto wdrożyć monitorowanie:

- procentu wolnego miejsca na dyskach,
- wolnego miejsca wewnątrz plików,
- liczby zdarzeń autogrowth,
- tempa wzrostu bazy,
- rozmiaru pliku logu,
- `log_reuse_wait_desc`,
- czasu trwania operacji rozszerzenia,
- maksymalnego rozmiaru plików.

Przykładowe poziomy ostrzegawcze mogą wyglądać następująco:

```text
poniżej 20% wolnego miejsca – ostrzeżenie,
poniżej 10% – alert krytyczny,
poniżej 5% – natychmiastowa reakcja.
```

Progi powinny jednak uwzględniać wielkość woluminu.

10% wolnego miejsca na dysku 100 GB to tylko 10 GB.

10% na dysku 10 TB to aż 1 TB.

Dlatego dobrze jest monitorować zarówno procent, jak i wartość bezwzględną.

## Podsumowanie

Włączony autogrowth nie oznacza, że SQL Server zawsze będzie mógł zwiększyć plik.

Mechanizm może nie zadziałać, gdy:

- na dysku brakuje miejsca,
- plik osiągnął `MAXSIZE`,
- filegroup jest pełna,
- przyrost jest większy niż wolna przestrzeń,
- występują problemy z uprawnieniami,
- storage posiada dodatkowe ograniczenia,
- problem dotyczy logu, który nie może zostać ponownie wykorzystany.

Najważniejsze jest rozdzielenie trzech pojęć:

1. rozmiar pliku,
2. wolne miejsce wewnątrz pliku,
3. wolne miejsce na dysku.

Autogrowth jest mechanizmem ochronnym.

Nie zastępuje monitoringu, planowania pojemności ani właściwego rozmiarowania plików.

Spokojny DBA nie czeka, aż baza wypełni cały dysk.

Spokojny DBA obserwuje trend, ustawia alerty i zwiększa przestrzeń, zanim brak miejsca stanie się incydentem produkcyjnym.
