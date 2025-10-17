---
title: "Dobry DBA nie zgaduje – obserwuje"
date: 2025-10-17
slug: dobry-dba-obserwuje
tags: [SQLServer, Monitoring, Grafana, InfluxDB, Telegraf, DevOps, DataPlatform]
draft: false
---

Każdy wykres to historia.  
CPU, I/O, pamięć, zapytania – wszystkie mówią, co naprawdę dzieje się na serwerze.  
Dobry DBA nie reaguje na alarm, tylko rozumie, *dlaczego* on się pojawił.  

Mój ulubiony zestaw: **Telegraf + InfluxDB + Grafana**.  
Z tego powstaje cockpit — **SQLManiak Monitoring**.  
Nie dashboard „bo ładny”, tylko **mapa świadomości systemu**, w której każda metryka ma znaczenie.

> „Wiedza zaczyna się tam, gdzie kończą się zgadywania.”

---

### Od reakcji do obserwacji

Większość problemów z wydajnością nie pojawia się nagle.  
One dojrzewają. Rosną cicho, pomiędzy kolejnymi `BACKUP`, `CHECKDB`, i zbyt długim `SELECT *`.  
Bez monitoringu widzimy tylko skutek – czerwony alert, rosnące czasy odpowiedzi, spadek PLE.  

Monitoring to nie magia.  
To **świadomość w czasie** – historia zdarzeń, która pozwala zobaczyć, jak serwer naprawdę żyje.  
Jeśli coś się psuje, to nie po to, by panikować, tylko by *zrozumieć*.

---

### Z czego zbudowany jest mój cockpit

Każdy składnik pełni określoną rolę:

- **Telegraf** – zbiera dane z SQL Servera, Windowsa, IIS-a i sieci.  
  Pluginy `inputs.sqlserver`, `inputs.win_perf_counters`, `inputs.tail` (dla logów IIS) i `inputs.ping` tworzą pełny obraz systemu.
  
- **InfluxDB** – magazyn czasowych serii metryk.  
  Każdy punkt to zdarzenie w czasie: `cpu_usage`, `wait_stats`, `tempdb_free_space`, `connections_active`.  
  Dzięki bucketom i retencji dane są zarówno *świeże*, jak i *historyczne*.

- **Grafana** – wizualizacja, czyli *lustro świadomości*.  
  Dashboardy pokazują trendy, a alerty wyłapują odchylenia od normy.  
  Nie chodzi o to, by było kolorowo, tylko by jedno spojrzenie wystarczyło do decyzji: *co dalej*.

---

### Co pokazuje dashboard

Mój dashboard podzielony jest na sekcje:

1. **System** – CPU, RAM, I/O, sieć.  
   Widać tu oddech serwera, rytm pracy i zużycie zasobów.
2. **SQL Server** – PLE, PAGEIOLATCH, THREADPOOL, tempdb usage, aktywne sesje.  
   Tutaj SQL zdradza, co go boli.
3. **Storage i logi** – opóźnienia dysków, write latency, IOPS, i statystyki dziennika transakcji.  
   Miejsce, gdzie kończy się teoria, a zaczyna fizyka.
4. **Query Insights** – top 10 zapytań według czasu CPU, log. reads i writes.  
   Tu widać, kto naprawdę zjada czas procesora.
5. **Alerty i Anomalie** – progi i trendy, które wyłapują nietypowe zachowania.  
   Niezawodność zaczyna się od świadomości, że coś *odbiega od normy*.

---

### Dlaczego nie wystarczy Performance Monitor

Bo wykresy z `perfmon.msc` mówią, że „coś się dzieje”, ale nie *dlaczego*.  
Grafana pozwala zestawić kontekst: CPU vs sesje, I/O vs query, pamięć vs tempdb.  
To właśnie **zderzenie wykresów** ujawnia zależności, których pojedyncze liczniki nigdy nie pokażą.  

Nie zgadujesz, nie panikujesz, tylko patrzysz — i widzisz.

---

### Filozofia obserwacji

Bycie DBA to trochę jak bycie astrofizykiem:  
Nie możesz zatrzymać gwiazdy, ale możesz rozumieć, czemu świeci inaczej niż wczoraj.  

SQL Server to też żywy organizm.  
Ma rytm, pamięć, kaprysy, i własne tempo reakcji.  
Zrozumienie przychodzi dopiero wtedy, gdy przestajesz patrzeć na błędy, a zaczynasz patrzeć na *przyczyny*.

> „Monitorowanie nie jest narzędziem. To sposób myślenia.”

---

### Eksperyment

Zainstaluj lokalnie:
```bash
choco install telegraf influxdb grafana
```

Skonfiguruj:
```toml
[[outputs.influxdb_v2]]
  urls = ["http://localhost:8086"]
  token = "$INFLUX_TOKEN"
  organization = "Demo"
  bucket = "Monitoring"
```

Dodaj plugin:
```toml
[[inputs.sqlserver]]
  servers = ["Server=localhost;User ID=telegraf;Password=Secret;app name=SQLMonitor"]
```

Uruchom Grafanę, dodaj źródło danych InfluxDB i zaimportuj dashboard.  
Pierwszy widok zawsze zaskakuje — nagle serwer *zaczyna mówić*.  

---

Zrozumienie jest początkiem kontroli.  
Dobry DBA nie zgaduje — obserwuje.  
I właśnie dlatego jego serwery są spokojne, nawet wtedy, gdy świat dookoła płonie.
