---
title: "EF Core 9: Viele-zu-viele-Beziehung mit zusätzlichen Feldern (Razor Pages)"
date: "2025-10-04"
slug: "efcore-9-many-to-many-extra-fields-de"
draft: false
description: "Ein Viele-zu-viele-Beispiel mit expliziter Verknüpfungsentität, Grade, EnrolledDate und UI-Validierung."
tags: ["EF Core","Razor Pages","Beziehungen"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/efcore-9-many-to-many-extra-fields.png"

---

## Einleitung
Eine einfache Viele-zu-viele-Beziehung ist unkompliziert. Eine Verknüpfungsentität mit zusätzlichen Feldern braucht jedoch mehr Aufmerksamkeit. Wir verbinden Student und Subject über Enrollment (Grade, EnrolledDate) mit Razor Pages.

## Modelle
```csharp
public class Student { public int Id {get;set;} public string Name {get;set;} = ""; public List<Enrollment> Enrollments {get;set;} = []; }
public class Subject { public int Id {get;set;} public string Title {get;set;} = ""; public List<Enrollment> Enrollments {get;set;} = []; }
public class Enrollment {
  public int StudentId {get;set;}
  public int SubjectId {get;set;}
  public decimal? Grade {get;set;}
  public DateTime EnrolledDate {get;set;} = DateTime.UtcNow;
  public Student Student {get;set;} = default!;
  public Subject Subject {get;set;} = default!;
}
```

## Konfiguration
```csharp
modelBuilder.Entity<Enrollment>().HasKey(e => new { e.StudentId, e.SubjectId });
modelBuilder.Entity<Enrollment>()
  .HasOne(e=>e.Student).WithMany(s=>s.Enrollments).HasForeignKey(e=>e.StudentId);
modelBuilder.Entity<Enrollment>()
  .HasOne(e=>e.Subject).WithMany(s=>s.Enrollments).HasForeignKey(e=>e.SubjectId);
```

## Validierung und UI
- Grade: Bereich 2,0–5,0, Schrittweite 0,5.
- Dropdowns für Student und Subject; Standarddatum ist *UTC Now*.
- Sortierung nach Subject und Filterung nach Student.

> Bereit für das Repository: Ergänze `DbInitializer`, Seed-Daten und eine Seite `/Enrollments/Create` mit `DataAnnotations`-Validierung.
