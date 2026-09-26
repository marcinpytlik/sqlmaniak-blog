---
title: "Konta usług SQL Server — domenowe, gMSA i minimalne uprawnienia"
date: 2026-12-15T20:00:00+01:00
slug: sql-server-service-accounts-gmsa
description: "Jak podejść do kont usług SQL Server, rozdzielenia Engine i Agent, gMSA, SPN oraz zasady najmniejszych uprawnień."
tags: [SQLServer, Security, gMSA, ServiceAccounts, DBA]
categories: [SQL Server]
draft: false
---

Konto usługi SQL Server nie jest tylko wpisem w `services.msc`.

Wpływa na uwierzytelnianie, dostęp do zasobów sieciowych, SPN i bezpieczeństwo całej instancji.

## Oddziel Engine i Agent

Jeżeli to możliwe, używaj osobnych kont dla SQL Server Database Engine i SQL Server Agent.

## Dlaczego gMSA?

Group Managed Service Account pozwala korzystać z konta domenowego bez ręcznego zarządzania hasłem.

Ogranicza to problem wygasających haseł, ręcznej rotacji i przechowywania haseł w dokumentacji.

## Sprawdź konto usługi

```sql
SELECT
    servicename,
    service_account,
    startup_type_desc,
    status_desc
FROM sys.dm_server_services;
```

## Dostęp do udziałów sieciowych

Jeżeli SQL Server wykonuje backup na udział UNC, dostęp do udziału musi mieć konto usługi Database Engine.

## SQL Server Agent i Proxy

Dla PowerShell, CmdExec czy SSIS można użyć Credential i Proxy, aby ograniczyć prawa konkretnego zadania.

## SPN

Przy uwierzytelnianiu Kerberos sprawdź SPN dla usługi SQL Server. Błędny lub zdublowany SPN może prowadzić do fallbacku do NTLM albo problemów z uwierzytelnianiem.

## Minimalne uprawnienia

Konto usługi nie powinno być Domain Admin ani lokalnym administratorem bez uzasadnienia.

## Podsumowanie

gMSA upraszcza zarządzanie hasłem, ale nadal trzeba dobrze zaprojektować uprawnienia, SPN, dostęp do sieci i rozdzielenie odpowiedzialności.