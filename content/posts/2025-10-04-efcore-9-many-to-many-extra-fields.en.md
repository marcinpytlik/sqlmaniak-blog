---
title: "EF Core 9: many-to-many relationships with extra fields (Razor Pages)"
date: "2025-10-04"
slug: "efcore-9-many-to-many-extra-fields-en"
draft: false
description: "A many-to-many example with an explicit join entity containing Grade and EnrolledDate, plus UI validation."
tags: ["EF Core","Razor Pages","Relationships"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/efcore-9-many-to-many-extra-fields.png"

---

## Introduction
A plain many-to-many relationship is easy, but a join entity with additional fields needs more care. We'll connect Student and Subject through Enrollment (Grade, EnrolledDate), using Razor Pages.

## Models
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

## Configuration
```csharp
modelBuilder.Entity<Enrollment>().HasKey(e => new { e.StudentId, e.SubjectId });
modelBuilder.Entity<Enrollment>()
  .HasOne(e=>e.Student).WithMany(s=>s.Enrollments).HasForeignKey(e=>e.StudentId);
modelBuilder.Entity<Enrollment>()
  .HasOne(e=>e.Subject).WithMany(s=>s.Enrollments).HasForeignKey(e=>e.SubjectId);
```

## Validation and UI
- Grade: range 2.0–5.0, increment 0.5.
- Student and Subject dropdowns; default date is *UTC Now*.
- Sort by Subject and filter by Student.

> Ready for a repository: add `DbInitializer`, seed data and an `/Enrollments/Create` page with `DataAnnotations` validation.
