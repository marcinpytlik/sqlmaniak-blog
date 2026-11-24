---
title: "How to Track SQL Server Versions, CUs, and GDRs Across Multiple Instances"
date: 2026-09-08
slug: track-sql-server-versions-cu-gdr-across-instances
description: "A practical approach to inventorying SQL Server builds, distinguishing CUs from GDRs, and planning patching across many instances."
tags: [SQLServer, CU, GDR, Patching, DBA, Security]
categories: [SQL Server]
draft: false
---

Patching one SQL Server instance is a technical task.

Patching dozens of instances becomes a management process.

## Reading the Instance Version

```sql
SELECT
    @@SERVERNAME AS ServerName,
    SERVERPROPERTY('ProductVersion') AS ProductVersion,
    SERVERPROPERTY('ProductLevel') AS ProductLevel,
    SERVERPROPERTY('Edition') AS Edition,
    SERVERPROPERTY('ProductUpdateLevel') AS ProductUpdateLevel,
    SERVERPROPERTY('ProductUpdateReference') AS ProductUpdateReference;
```

The full build number matters most. Simply saying “SQL Server 2022” is not enough.

## CU and GDR

A CU is a cumulative set of fixes. GDR updates mainly address security and critical fixes for a particular servicing branch.

The most important rule:

> Compare the complete build number against your organization's approved baseline.

## Baseline Table

```sql
CREATE SCHEMA patch;
GO

CREATE TABLE patch.SqlBuildBaseline
(
    SqlBuildBaselineId int IDENTITY(1,1) NOT NULL,
    MajorVersion int NOT NULL,
    ProductVersion varchar(50) NOT NULL,
    UpdateType varchar(20) NOT NULL,
    UpdateName varchar(100) NULL,
    ReleaseDate date NULL,
    IsApproved bit NOT NULL,
    IsCurrentTarget bit NOT NULL,
    Notes nvarchar(1000) NULL,
    CONSTRAINT PK_SqlBuildBaseline
        PRIMARY KEY CLUSTERED (SqlBuildBaselineId),
    CONSTRAINT UQ_SqlBuildBaseline_ProductVersion
        UNIQUE (ProductVersion)
);
GO
```

## Patching History

Record:

- the build before the update,
- the build after the update,
- start and finish times,
- status,
- change request number,
- validation result,
- whether a restart occurred.

## Post-Patching Validation

Check:

- engine version,
- service status,
- SQL Server Error Log,
- database states,
- Always On or FCI,
- SQL Server Agent,
- critical jobs,
- Database Mail,
- backups,
- monitoring.

```sql
SELECT
    name,
    state_desc,
    user_access_desc,
    recovery_model_desc
FROM sys.databases
ORDER BY name;
```

## Complete Process

1. Inventory.
2. Select the target build.
3. Analyze requirements.
4. Test in a lab.
5. Prepare a rollback plan.
6. Schedule a maintenance window.
7. Install the update.
8. Restart.
9. Validate.
10. Update documentation.

## Summary

Controlling CUs and GDRs requires a central inventory, a baseline, history, and validation.

A calm DBA does not patch from memory.

They patch the fleet based on data, standards, and a documented process.
