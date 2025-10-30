---
title: "HOBT – hierarchia porządku danych"
date: 2025-10-30
slug: hobt-anatomia
tags: [SQLServer, Internals, Indexes, HOBT, Storage]
draft: false
---
Dane w SQL Serverze nie leżą luzem. Tworzą drzewa, a ich gałęzie prowadzą do stron danych.
HOBT (Heap Or B-Tree) to jednostka składowania stojąca za każdym indeksem B-tree i za każdą tabelą heap (bez klastrowanego). To „szkielet” porządku i adresowania danych — od korzenia (root), przez poziomy pośrednie, aż po liście (leaf).

„Struktura jest formą istnienia porządku.” — SQLManiak

Co to jest HOBT w praktyce?

Każda partycja indeksu lub heap’a = jeden HOBT.
(tabela 1-partycja i 3 indeksy ⇒ 4 HOBT; tabela 4-partycje i 2 indeksy ⇒ 8 HOBT).

HOBT ≠ indeks jako obiekt — to fizyczne drzewo/układ stron i przydziałów dla danej partycji indeksu/heap’a.

Identyfikator HOBT: hobt_id (stabilny w czasie istnienia, ale może się zmienić po niektórych operacjach odbudowy/przebudowy).

HOBT a jednostki przydziału (Allocation Units)

Każdy HOBT może mieć do 3 allocation units:

IN_ROW_DATA – wiersze mieszczące się w 8 KB strony,

ROW_OVERFLOW_DATA – dane przepełnione (kolumny VARCHAR/NVARCHAR/VARBINARY przekraczające limit wiersza),

LOB_DATA – obiekty LOB (XML, (N)TEXT*, VARBINARY(MAX), itp.).

Powiązanie: sys.allocation_units.container_id = sys.partitions.hobt_id.

Heapy vs B-tree — co się różni?

Heap: brak klucza klastra, liściem są strony danych NIEPOSORTOWANE logicznie; możliwe „forwarded records” (przekierowania) przy aktualizacjach zwiększających rozmiar wiersza.

B-tree (index): uporządkowana struktura; liść klastrowanego indeksu = strony danych tabeli; liść nieklastrowanego = strony z kluczami + wskaźniki (RID lub klucz klastra).

Mapka stron i metadane

Metadane i mapy: PFS (Page Free Space), GAM/SGAM (alokacje extentów), IAM (Index Allocation Map) spinają HOBT z przydzielonymi stronami.

Diagnostyka drzewa: sys.dm_db_index_physical_stats (poziomy, fragmentacja, forwarded), sys.dm_db_database_page_allocations (szczegóły alokacji, nieudokumentowane), DBCC PAGE/IND (głębokie nurkowanie — nieudokumentowane).

🔍 Szybkie DMV: HOBT w Twojej bazie
-- Przegląd HOBT-ów: tabela/indeks/partycja → HOBT → allocation units
SELECT
  o.name              AS ObjectName,
  i.name              AS IndexName,
  i.index_id,
  p.partition_number,
  p.hobt_id,
  au.type_desc        AS AU_Type,
  au.total_pages,
  au.used_pages
FROM sys.partitions AS p
JOIN sys.objects   AS o  ON o.object_id = p.object_id
LEFT JOIN sys.indexes   AS i  ON i.object_id = p.object_id AND i.index_id = p.index_id
LEFT JOIN sys.allocation_units AS au ON au.container_id = p.hobt_id
WHERE o.type = 'U'
ORDER BY ObjectName, IndexName, partition_number, AU_Type;

Poziomy drzewa i statystyki fizyczne
-- Poziomy B-tree, liczba stron, forwarded records (dla heapów)
SELECT
  OBJECT_NAME(ips.object_id) AS ObjectName,
  ips.index_id,
  ips.index_type_desc,
  ips.index_level,
  ips.page_count,
  ips.record_count,
  ips.avg_page_space_used_in_percent,
  ips.forwarded_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED') AS ips
ORDER BY ObjectName, index_id, index_level DESC;

Które heapy mają przekierowane wiersze?
SELECT
  OBJECT_NAME(object_id) AS HeapName,
  forwarded_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, 0, NULL, 'SAMPLED')
WHERE index_id = 0                      -- heap
  AND forwarded_record_count > 0
ORDER BY forwarded_record_count DESC;

🧪 Lab: zobacz HOBT w działaniu (kopiuj-wklej)
USE tempdb;
GO
IF OBJECT_ID('dbo.HobtDemo') IS NOT NULL DROP TABLE dbo.HobtDemo;
GO

-- 1) Start: HEAP
CREATE TABLE dbo.HobtDemo
(
  Id       INT IDENTITY(1,1) NOT NULL,
  K1       INT NOT NULL,
  Payload  VARCHAR(100) NULL
);
GO

INSERT dbo.HobtDemo(K1, Payload)
SELECT TOP (5000) ABS(CHECKSUM(NEWID())) % 100, REPLICATE('x', 50)
FROM sys.all_objects a CROSS JOIN sys.all_objects b;

-- HOBT dla heapa
SELECT p.hobt_id, p.partition_number, au.type_desc, au.total_pages, au.used_pages
FROM sys.partitions p
JOIN sys.allocation_units au ON au.container_id = p.hobt_id
WHERE p.object_id = OBJECT_ID('dbo.HobtDemo')
ORDER BY au.type_desc;

-- 2) Dodaj indeks nieklastrowany (drugi HOBT)
CREATE INDEX IX_HobtDemo_K1 ON dbo.HobtDemo(K1);

SELECT i.name, i.index_id, p.hobt_id
FROM sys.indexes i
JOIN sys.partitions p ON p.object_id = i.object_id AND p.index_id = i.index_id
WHERE i.object_id = OBJECT_ID('dbo.HobtDemo')
ORDER BY i.index_id;

-- 3) Zamień na indeks klastrowany (heap → B-tree) – zmienia się układ HOBT
CREATE CLUSTERED INDEX CX_HobtDemo_Id ON dbo.HobtDemo(Id);

SELECT i.name, i.index_id, p.hobt_id
FROM sys.indexes i
JOIN sys.partitions p ON p.object_id = i.object_id AND p.index_id = i.index_id
WHERE i.object_id = OBJECT_ID('dbo.HobtDemo')
ORDER BY i.index_id;

-- 4) Poziomy drzewa po zmianie
SELECT ips.index_type_desc, ips.index_level, ips.page_count, ips.record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.HobtDemo'), NULL, NULL, 'DETAILED') ips
ORDER BY index_level DESC;


🔎 Uwaga: po przejściu z heap’a na indeks klastrowany układ stron i identyfikatory mogą się zmienić (w tym hobt_id). To normalne.

🧭 Lokalizacja fizyczna wiersza (RID/klucz klastra)

Czasem chcesz „dotknąć” konkretnej strony. Pomagają pseudokolumny i funkcje:

-- Gdzie leży dany wiersz? (potrzebne uprawnienia VIEW SERVER STATE)
SELECT TOP (10)
  %%physloc%% AS FilePageSlot,
  sys.fn_PhysLocFormatter(%%physloc%%) AS Formatted,
  *
FROM dbo.HobtDemo
ORDER BY Id;


A jeśli chcesz iść głębiej (dla labu, ostrożnie w prod):

-- NIEUDOKUMENTOWANE: czytaj strony (wymaga TF 3604)
DBCC TRACEON(3604);
-- DBCC PAGE (db_id, file_id, page_id, printopt)
-- DBCC IND pokazuje listę stron dla obiektu
-- DBCC IND (DB_ID(), 'dbo.HobtDemo', 1);

Typowe „zapachy” i szybkie remedia
1) Heap z forwarded records

Objaw: forwarded_record_count > 0

Skutek: dodatkowe skoki stron = gorsze I/O

Remedium: przebuduj do klastrowanego (jeśli to ma sens), ewentualnie ALTER TABLE ... REBUILD/ALTER INDEX ... REBUILD lub zaprojektuj docelowy klucz klastra.

2) Zbyt głębokie drzewo (dużo poziomów)

Objaw: index_level wysoki, page_count duży

Skutek: więcej odczytów pośrednich

Remedium: przegląd klucza (szerokość i selektywność), fillfactor, partycjonowanie, kompresja stron/wierszy.

3) Nadmiar ROW_OVERFLOW/LOB

Objaw: duże ROW_OVERFLOW_DATA/LOB_DATA w sys.allocation_units

Skutek: dodatkowe skoki przy odczycie wiersza

Remedium: projekt kolumn (np. krótsze NVARCHAR, separacja kolumn rzadko używanych, archiwizacja), ewentualnie kompresja.

🧰 Checklista DBA (HOBT-aware)

Inwentaryzacja HOBT (DMV sys.partitions + sys.allocation_units).

Poziomy i fragmentacja (sys.dm_db_index_physical_stats).

Heapy z przekierowaniami — szybka lista do przebudowy.

Rozmiary AU (IN_ROW_DATA/ROW_OVERFLOW_DATA/LOB_DATA).

Plan przebudów (REBUILD/REORGANIZE, zmiana klucza klastra, partycje).

Monitoring: dorzuć metryki z DMV do Twojej Grafany (page_count, forwarded, avg_page_space).

Przykładowy „pakiet metryk” do widoku:

CREATE OR ALTER VIEW dbo.vHobtHealth AS
SELECT
  DB_NAME()                         AS DbName,
  OBJECT_SCHEMA_NAME(p.object_id)   AS SchemaName,
  OBJECT_NAME(p.object_id)          AS ObjectName,
  i.index_id,
  ISNULL(i.name, '(HEAP)')          AS IndexName,
  p.partition_number,
  p.hobt_id,
  au_in.total_pages                 AS InRowPages,
  au_ro.total_pages                 AS RowOverflowPages,
  au_lob.total_pages                AS LobPages,
  ips.page_count,
  ips.record_count,
  ips.index_level,
  ips.avg_page_space_used_in_percent,
  ips.forwarded_record_count
FROM sys.partitions p
LEFT JOIN sys.indexes i ON i.object_id = p.object_id AND i.index_id = p.index_id
OUTER APPLY (SELECT SUM(total_pages) AS total_pages FROM sys.allocation_units WHERE container_id = p.hobt_id AND type_desc='IN_ROW_DATA') au_in
OUTER APPLY (SELECT SUM(total_pages) AS total_pages FROM sys.allocation_units WHERE container_id = p.hobt_id AND type_desc='ROW_OVERFLOW_DATA') au_ro
OUTER APPLY (SELECT SUM(total_pages) AS total_pages FROM sys.allocation_units WHERE container_id = p.hobt_id AND type_desc='LOB_DATA') au_lob
OUTER APPLY (SELECT TOP (1) * 
  FROM sys.dm_db_index_physical_stats(DB_ID(), p.object_id, p.index_id, p.partition_number, 'SAMPLED') 
) ips;
GO

Podsumowanie

HOBT to punkt, w którym logika indeksu spotyka się z fizyką stron. Rozumiejąc hobt_id i powiązane allocation units:

wiesz, gdzie Twoje wiersze naprawdę żyją,

potrafisz diagnozować forwarded records, głębokość drzewa i fragmentację,

projektujesz klucze klastrowane i partycje świadomie, a nie „na czuja”.

🔧 TL;DR – narzędziówka

sys.partitions.hobt_id ⇄ sys.allocation_units.container_id

sys.dm_db_index_physical_stats — poziomy, fragmentacja, forwarded

sys.dm_db_database_page_allocations — alokacje stron (deep dive)

%%physloc%%, fn_PhysLocFormatter — lokalizacja wiersza

(opcjonalnie) DBCC IND/PAGE — diagnostyka stron (na labie)