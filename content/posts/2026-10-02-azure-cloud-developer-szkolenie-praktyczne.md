---
title: "Azure Cloud Developer — 5-dniowe szkolenie praktyczne"
date: "2026-10-02"
slug: "azure-cloud-developer-szkolenie-praktyczne"
draft: false
description: "Praktyczne 5-dniowe szkolenie Azure dla developerów .NET: App Service, Storage, Functions, Cosmos DB, containers, Managed Identity, Key Vault, Service Bus, Event Grid, API Management, monitoring, Bicep i CI/CD."
tags: ["Azure", ".NET", "App Service", "Azure Functions", "Service Bus", "Cosmos DB", "API Management", "Szkolenia"]
author: "Marcin Pytlik | SQLManiak"
canonical: "https://sqlmaniak.blog/posts/azure-cloud-developer-szkolenie-praktyczne/"
---

Tworzenie aplikacji w Azure nie polega na przeniesieniu lokalnego projektu do chmury i kliknięciu Deploy.

Developer powinien rozumieć, jak aplikacja korzysta z compute, storage, identity, messaging, observability i automatyzacji infrastruktury — oraz jak projektować ją tak, żeby sekrety nie trafiały do kodu, awarie usług zewnętrznych nie zatrzymywały całego systemu, a problemy można było później zdiagnozować.

Właśnie temu służy moje szkolenie **„Azure Cloud Developer”** — pięć dni praktycznej pracy z aplikacją .NET działającą w Azure.

Szkolenie nawiązuje zakresem do kompetencji znanych z dawnego AZ-204, ale nie jest oficjalnym kursem egzaminacyjnym. Jest projektowane jako współczesny, praktyczny warsztat developerski.

## Dla kogo jest to szkolenie?

Szkolenie jest przeznaczone dla:
- programistów .NET pracujących z Azure,
- developerów backend,
- zespołów przenoszących aplikacje do chmury,
- osób budujących rozwiązania serverless i event-driven,
- developerów odpowiedzialnych za integrację, bezpieczeństwo i monitoring aplikacji.

Uczestnik powinien znać C#, podstawy ASP.NET Core oraz komunikację HTTP.

## Program — 5 dni

### Dzień 1 — App Service, deployment i Storage

- architektura aplikacji w Azure,
- Resource Groups,
- Azure App Service,
- deployment aplikacji,
- deployment slots,
- konfiguracja per environment,
- Azure Storage,
- Blob Storage,
- dostęp do Storage z .NET.

### Dzień 2 — Azure Functions i Cosmos DB

- Azure Functions,
- HTTP Trigger,
- Timer Trigger,
- Blob Trigger,
- Queue Trigger,
- serverless patterns,
- Azure Cosmos DB,
- SDK .NET,
- partitioning,
- Request Units.

### Dzień 3 — containers, identity i secrets

- containers w Azure,
- Azure Container Registry,
- Azure Container Apps,
- deployment obrazów,
- Microsoft Entra ID,
- Managed Identity,
- Azure Key Vault,
- DefaultAzureCredential,
- eliminowanie sekretów i connection stringów z kodu.

### Dzień 4 — messaging i integracja

- Azure Service Bus,
- queues,
- topics i subscriptions,
- Event Grid,
- event-driven architecture,
- API Management,
- policies,
- zabezpieczenie i publikacja API.

### Dzień 5 — observability, resilience, IaC i Cloud Capstone

- Application Insights,
- Azure Monitor,
- distributed tracing,
- OpenTelemetry,
- retry i resilience,
- Bicep,
- podstawy CI/CD,
- końcowy Cloud Capstone.

## Cloud Capstone

Końcowa architektura łączy:
- API Management,
- ASP.NET Core Web API,
- Service Bus,
- Worker lub Azure Function,
- Cosmos DB,
- Blob Storage,
- Managed Identity,
- Key Vault,
- Application Insights,
- Azure Monitor,
- Bicep.

Uczestnik wdraża rozwiązanie, generuje kontrolowany problem, diagnozuje go i potwierdza poprawne recovery.

## Co odróżnia to szkolenie od starego modelu AZ-204?

Nie koncentrujemy się na odtwarzaniu kroków w Azure Portal.

Większy nacisk jest położony na:
- Managed Identity zamiast sekretów w konfiguracji,
- DefaultAzureCredential,
- Container Apps,
- event-driven architecture,
- observability,
- resilience,
- Infrastructure as Code,
- automatyzację deploymentu,
- analizę awarii i zachowania systemu.

## Rezultat szkolenia

Po szkoleniu uczestnik potrafi zaprojektować, wdrożyć, zabezpieczyć i monitorować aplikację .NET w Azure oraz świadomie dobrać App Service, Functions, containers, Storage, Cosmos DB, messaging i API Management do konkretnego problemu.

## Forma organizacyjna

Szkolenie trwa **5 dni** i może być prowadzone stacjonarnie lub online.

Pełny opis usług znajdziesz w sekcji **[Oferta](/oferta/)**.

Możesz też **[skontaktować się ze mną bezpośrednio](/contact/)** i opisać stos aplikacyjny, doświadczenie zespołu oraz oczekiwany rezultat szkolenia.
