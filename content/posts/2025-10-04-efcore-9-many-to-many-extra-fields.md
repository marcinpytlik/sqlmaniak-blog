---
title: "EF Core 9: relacja wiele‑do‑wielu z dodatkowymi polami (Razor Pages)"
date: "2025-10-04"
slug: "efcore-9-many-to-many-extra-fields"
draft: false
description: "Prosty przykład many‑to‑many z tabelą łącznikową, która ma własne kolumny (Grade, EnrolledDate) i walidację po stronie UI."
tags: ["EF Core", "C# .NET 9", "Razor Pages", "Relacje", "ORM"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/efcore-9-many-to-many-extra-fields.png"
canonical: "https://sqlmaniak.blog/efcore-9-many-to-many-extra-fields"
---

Lead
----
„Gołe” many‑to‑many to banał, ale „łącznik” z dodatkowymi polami już nie. Zrobimy Student–Subject przez Enrollment (Grade, EnrolledDate) + Razor Pages.

## Modele
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

## Konfiguracja
```csharp
modelBuilder.Entity<Enrollment>().HasKey(e => new { e.StudentId, e.SubjectId });
modelBuilder.Entity<Enrollment>()
  .HasOne(e=>e.Student).WithMany(s=>s.Enrollments).HasForeignKey(e=>e.StudentId);
modelBuilder.Entity<Enrollment>()
  .HasOne(e=>e.Subject).WithMany(s=>s.Enrollments).HasForeignKey(e=>e.SubjectId);
```

## Walidacja i UI
- Grade: zakres 2.0–5.0, krok 0.5.  
- Dropdowny Student/Subject, data domyślnie *UTC Now*.
- Sortowanie po Subject, filtrowanie po Student.

> Repo‑ready: dodaj `DbInitializer`, seedy i stronę `/Enrollments/Create` z walidacją `DataAnnotations`.
