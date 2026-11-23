---
description: >-
  StepUp RepRep 4.2 is the last release of the package,
  whose features will move to three smaller packages for documents, data and notebooks.
  This page explains what changes, why, and what to do in the meantime.
---

<!--
SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Package Split

!!! warning "StepUp RepRep 4.2 is the final release."

    There will be no further releases of StepUp RepRep.
    Fixes and new features will only appear in the packages that replace it.

## What Changes

StepUp RepRep 4.2 is the last release of this package.
Its features will move to smaller packages.
More details will be added here when they are released.

## Why

StepUp RepRep groups unrelated tools for historical reasons.
Everyone who installs it also gets heavy dependencies, such as Jupyter and WeasyPrint,
even when they only need a small part of its features.
The smaller packages will have a clearer purpose,
and will be easier to install, to maintain and to extend.

## What to Do Now

The following features are deprecated in 4.2 and will not move to the new packages:

- [`wrap_git()`][stepup.reprep.api.wrap_git] and `srr-wrap-git`
- [`execute_papermill()`][stepup.reprep.api.execute_papermill] and `srr-execute-papermill`
- [`convert_mutool()`][stepup.reprep.api.convert_mutool]
  and [`convert_mutool_png()`][stepup.reprep.api.convert_mutool_png]
- [`convert_odf_pdf()`][stepup.reprep.api.convert_odf_pdf]
- `srr-normalize-pdf`

The [changelog](changelog.md) explains how to replace each of them.
Moving away from these features now makes the migration to the new packages easier later.

## Migration

A migration guide will appear on this page when the new packages are released.
The first releases of the new packages will be able to read the files written by StepUp RepRep 4.2,
such as inventory files and the Zenodo configuration.
