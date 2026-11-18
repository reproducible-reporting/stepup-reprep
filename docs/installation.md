---
description: >-
  Install StepUp RepRep with pip on Linux, macOS or Windows, on Python 3.11 or later,
  which also installs StepUp Core,
  and find out which functions are tested on Windows and what they need there.
---

<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Installation

!!! warning "The installation instructions are listed here for completeness."

    If you are new to StepUp RepRep,
    we recommend that you follow the [Template Tutorial](from_template/introduction.md) instead.
    One of the steps in that tutorial is to install StepUp RepRep in a suitable virtual environment.

## Requirements

- Linux, macOS or Windows.
  [Supported Platforms][core-platforms] in the documentation of StepUp Core
  explains what differs between them.
  [Windows](#windows) below adds what is specific to StepUp RepRep.
- [Python](https://www.python.org/) ≥ 3.11.
  On Windows, StepUp Core recommends a minimal patch release for security reasons,
  see its [installation instructions][core-installation].
- [Pip](https://pip.pypa.io/)

It is assumed you know how to use [Pip](https://pip.pypa.io/).
We recommend performing the installation
in a [Python virtual environment](https://docs.python.org/3/library/venv.html)
and activating such environments with [direnv](https://direnv.net/).

## Minimal Installation

The RepRep extension (for reproducible reporting) is installed with:

```bash
pip install stepup-reprep
```

(This will also install [StepUp Core](https://reproducible-reporting.github.io/stepup-core/).)

## Windows

StepUp RepRep runs natively on Windows, without WSL.
The [Windows section of Supported Platforms][core-windows]
explains what a workflow has to take care of on Windows,
e.g. how to put a path into a command.
The rest of this section is specific to StepUp RepRep.

### Tested Functions

The test suite runs on Windows for the following functions of `stepup.reprep.api`,
with Tectonic 0.17 and Typst 0.15 as the only external programs:

- [`add_notes_pdf()`][stepup.reprep.api.add_notes_pdf]
- [`cat_pdf()`][stepup.reprep.api.cat_pdf]
- [`check_hrefs()`][stepup.reprep.api.check_hrefs]
- [`compile_tectonic()`][stepup.reprep.api.compile_tectonic]
- [`compile_typst()`][stepup.reprep.api.compile_typst]
- [`convert_jupyter()`][stepup.reprep.api.convert_jupyter]
- [`convert_markdown()`][stepup.reprep.api.convert_markdown]
- [`execute_papermill()`][stepup.reprep.api.execute_papermill]
- [`flatten_latex()`][stepup.reprep.api.flatten_latex]
- [`make_inventory()`][stepup.reprep.api.make_inventory]
- [`nup_pdf()`][stepup.reprep.api.nup_pdf]
- [`raster_pdf()`][stepup.reprep.api.raster_pdf]
- [`sanitize_bibtex()`][stepup.reprep.api.sanitize_bibtex]
- [`sync_zenodo()`][stepup.reprep.api.sync_zenodo]
- [`unplot()`][stepup.reprep.api.unplot]
- [`wrap_git()`][stepup.reprep.api.wrap_git]
- [`zip_inventory()`][stepup.reprep.api.zip_inventory]

### Untested Functions

The following functions are not tested on Windows,
because the programs or libraries they need are not installed for the tests:

- [`compile_latex()`][stepup.reprep.api.compile_latex]
  needs a LaTeX distribution, such as TeX Live.
- [`convert_inkscape()`][stepup.reprep.api.convert_inkscape],
  [`convert_inkscape_pdf()`][stepup.reprep.api.convert_inkscape_pdf]
  and [`convert_inkscape_png()`][stepup.reprep.api.convert_inkscape_png]
  need Inkscape.
- [`convert_mutool()`][stepup.reprep.api.convert_mutool]
  and [`convert_mutool_png()`][stepup.reprep.api.convert_mutool_png]
  need `mutool` from MuPDF.
- [`convert_odf_pdf()`][stepup.reprep.api.convert_odf_pdf]
  needs LibreOffice and a [POSIX shell](#posix-shell).
- [`convert_weasyprint()`][stepup.reprep.api.convert_weasyprint]
  needs the [libraries of WeasyPrint](#weasyprint).
- [`diff_latex()`][stepup.reprep.api.diff_latex]
  needs `latexdiff` and a [POSIX shell](#posix-shell).

### POSIX Shell

[`convert_odf_pdf()`][stepup.reprep.api.convert_odf_pdf]
and [`diff_latex()`][stepup.reprep.api.diff_latex] create steps that run in a shell,
and so does [`wrap_git()`][stepup.reprep.api.wrap_git] with `shell=True`.
On Windows, such steps need a POSIX shell, e.g. the one of Git for Windows,
see [POSIX Shell on Windows][core-posix-shell].
The other functions do not need a shell.

`convert_odf_pdf()` passes a temporary directory made by `mktemp` to LibreOffice,
inside a `file://` URL.
The shell of Git for Windows only converts arguments that look like POSIX paths,
so this URL may reach LibreOffice in a form that it cannot use.

### WeasyPrint

[`convert_weasyprint()`][stepup.reprep.api.convert_weasyprint] uses WeasyPrint,
which loads the Pango and GLib libraries of GTK, and the HarfBuzz-Subset library.
Pip does not install these libraries.
As of WeasyPrint 70.0, a missing HarfBuzz-Subset library only causes a `DeprecationWarning`,
but future versions of WeasyPrint will require it.
On Debian and Ubuntu, it is provided by the package `libharfbuzz-subset0`.
Install them as explained in the [documentation of WeasyPrint][weasyprint-windows].

### Jupyter Kernels

[`convert_jupyter()`][stepup.reprep.api.convert_jupyter]
and [`execute_papermill()`][stepup.reprep.api.execute_papermill]
communicate with their Jupyter kernel through ZeroMQ.
On Linux and macOS, they use IPC sockets in a private temporary directory.
On Windows, they use TCP ports on `127.0.0.1`,
because the Windows wheels of pyzmq have no IPC transport, as observed with pyzmq 27.3.
When many notebooks start at the same time,
a kernel may then fail to start with "Address already in use",
because Jupyter selects free ports before the kernel binds them.

### Tectonic

As observed with Tectonic 0.17,
Tectonic on Windows prints `Fontconfig error: Cannot load default config file` on every run,
unless the environment variable `FONTCONFIG_FILE` names a fontconfig configuration.
The steps of [`compile_tectonic()`][stepup.reprep.api.compile_tectonic] still succeed.
[Tests on Windows](development.md#tests-on-windows) shows how to set this variable.

### Text Files

All tools of StepUp RepRep read text files as UTF-8,
and write them as UTF-8 with `\n` line endings, on every platform.
Save your sources, e.g. LaTeX, Markdown and BibTeX files, as UTF-8.

### Inventories and ZIP Files

Windows has no permission bits.
An inventory made on Windows therefore records other file modes
than one made of the same files on Linux or macOS,
e.g. `-rw-rw-rw-` instead of `-rw-r--r--`.
[`zip_inventory()`][stepup.reprep.api.zip_inventory] stores these modes in the ZIP file,
so a ZIP file made on Windows also differs from one made on Linux or macOS.

`srr-check-inventory` only compares file modes on Linux and macOS.
An inventory made on Linux or macOS can be checked on Windows,
but one made on Windows fails the check on Linux and macOS as soon as a file mode differs.

[core-platforms]: https://reproducible-reporting.github.io/stepup-core/platforms/
[core-windows]: https://reproducible-reporting.github.io/stepup-core/platforms/#windows
[core-installation]: https://reproducible-reporting.github.io/stepup-core/installation/
[core-posix-shell]: https://reproducible-reporting.github.io/stepup-core/installation/#posix-shell-on-windows
[weasyprint-windows]: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows
