<!-- markdownlint-disable no-duplicate-heading -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Effort-based Versioning](https://jacobtomlinson.dev/effver/).
(Changes to features documented as "experimental" will not increment macro and meso version numbers.)

## [Unreleased][]

(no changes yet)

## [2.3.2][] - 2025-02-24 {: #v2.3.2 }

This release makes `compile_typst` compatible with Typst 0.13,
and drops support for markdown-katex.

### Added

- Configuration for development with [devenv](https://devenv.sh/)

### Changed

- Drop support for the ailing markdown_katex integration.
  (Typst can be used to achieve similar results much more efficiently).
- Update `compile_typst` for [Typst 0.13](https://github.com/typst/typst/releases/tag/v0.13.0)

## [2.3.1][] - 2025-02-12 {: #v2.3.1 }

This is a minor bugfix release.

### Fixed

- Remove some debug output.

## [2.3.0][] - 2025-02-12 {: #v2.3.0 }

This release adds support for Jupyter notebooks with `convert_jupyter()`
and introduces small breaking changes to the API.
Other noteworthy changes include new options to the `compile_typst()` function,
more ways to specify variables in `render_jinja()`.

### Added

- Execute and convert Jupyter notebooks with [`convert_jupyter()`][stepup.reprep.api.convert_jupyter].
- `rr-bibsane` is now part of StepUp RepRep, instead of using the (retired) `bibsane` package.
  The main difference, other than the improved integration with StepUp RepRep,
  is that journal abbreviations are now generated with [pyiso4](https://github.com/pierre-24/pyiso4)
  instead of the [abrevvIso](https://abbreviso.toolforge.org) Web API.
  It has a corresponding [`sanitize_bibtex()`][stepup.reprep.api.sanitize_bibtex] function
  in `stepup.reprep.api`.

### Changed

- Extend [`compile_typst()`][stepup.reprep.api.compile_typst] with additional options:
    - Specification of the output file.
    - Key-value pairs for the `--input` argument.
    - PNG and SVG output formats (multipage is not working yet).
    - Optional inventory output file.
    - Pass-through arguments for `typst`
- Breaking changes to existing API:
    - `convert_pdf()` and related functions are renamed:
        - `convert_pdf()` becomes [`convert_mutool()`][stepup.reprep.api.convert_mutool]
        - `convert_pdf_png()` becomes [`convert_mutool_png()`][stepup.reprep.api.convert_mutool_png]
    - `convert_svg()` and related functions are renamed:
        - `convert_svg()` becomes [`convert_inkscape()`][stepup.reprep.api.convert_inkscape]
        - `convert_svg_pdf()` becomes [`convert_inkscape_pdf()`][stepup.reprep.api.convert_inkscape_pdf]
        - `convert_svg_png()` becomes [`convert_inkscape_png()`][stepup.reprep.api.convert_inkscape_png]
    - The `inkscape_args` of [`convert_inkscape()`][stepup.reprep.api.convert_inkscape]
      must now be a list instead of a string.
    - [`compile_latex()`][stepup.reprep.api.compile_latex] no longer creates
      an inventory file by default.
      To recover the old behavior, add `inventory=True` to the arguments
      or set the environment variable `REPREP_LATEX_INVENTORY="1"`.
    - [`compile_latex()`][stepup.reprep.api.compile_latex] no longer calls `bibsane`
      when the LaTeX source has a BibTeX bibliography.
      If you want to sanitize the BibTeX file, call [`sanitize_bibtex()`][stepup.reprep.api.sanitize_bibtex]
      after `compile_latex()`.
    - The `paths_variables` argument of [`render_jinja()`][stepup.reprep.api.render_jinja]
      has been replaced by a variadic positional parameter (i.e. `*paths_variables`).
- Other changes
    - Change [`convert_weasyprint()`][stepup.reprep.api.convert_weasyprint]
      to perform the conversion in a single step.
    - Improve handling of arguments and dependencies in
      [`convert_markdown()`][stepup.reprep.api.convert_markdown]
    - [`render_jinja()`][stepup.reprep.api.render_jinja] now accepts JSON and YAML files
      with variables for Jinja2 templates.
      In addition, one may specify a dictionary with variables directly when calling the function.
    - Documentation improvements.

## [2.2.3][] - 2025-02-05 {: #v2.2.3 }

This release uses the new `STEPUP_EXTERNAL_SOURCES` environment variable
introduced in StepUp Core 2.0.6.

### Changed

- Switch from [SemVer](https://semver.org/spec/v2.0.0.html) to
  [EffVer](https://jacobtomlinson.dev/effver/).
- Scripts that automatically detect dependencies
  (`rr-compile-latex`, `rr-compile-typst` and `rr-convert-inkscape`)
  now also use the new `STEPUP_EXTERNAL_SOURCES` environment variable
  introduced in StepUp Core 2.0.6.

## [2.2.2][] - 2025-01-31 {: #v2.2.2 }

This is a bugfix release addressing minor issues in the Typst support.

### Fixed

- Only call `sys.exit` in `rr-compile-typst` if the returncode is non-zero.
  This allows for other scripts to call its main function without exiting
  in case of a succeeded typst build.

## [2.2.1][] - 2025-01-31 {: #v2.2.1 }

This is a bugfix release addressing minor issues in the Typst support.

### Fixed

- Fix returncode of the `rr-compile-typst` command (now passes through returncode of `typst build`).
- By default, depfiles created by `typst build` are now stored in a temporary directory,
  to avoid littering the working directory.
  You can keep depfiles by setting the environment variable `REPREP_KEEP_TYPST_DEPS="1"`,
  or with the argument `keep_deps=True` in [`compile_typst()`][stepup.reprep.api.compile_typst].
  (Either one will .)

## [2.2.0][] - 2025-01-29 {: #v2.2.0 }

This release adds experimental support for [typst](https://github.com/typst).
It also introduces a few breaking API changes for the sake of consistency.
(More breaking changes should be expected in the near future.)

### Added

- Experimental support for Typst.

### Changed

- Rename API functions:
    - `latex()` -> [`compile_latex()`][stepup.reprep.api.compile_latex]
    - `latex_flat()` -> [`flatten_latex()`][stepup.reprep.api.flatten_latex]
    - `latex_diff()` -> [`diff_latex()`][stepup.reprep.api.diff_latex]

## [2.1.0][] - 2025-01-27 {: #v2.1.0 }

This release contains a few minor breaking changes for the sake of internal consistency.

### Changed

- The conversion with Inkscape has become a single step.
  (It was first split up in a step scanning for dependencies followed by the actual conversion.)
- Add more entrypoints for command-line utilities in StepUp RepRep.
  Existing ones were renamed from `reprep-*` to `rr-*`.
- Rename module `stepup.reprep.render` to `stepup.reprep.render_jinja`.
- Rename API function: `render()` -> [`render_jinja()`][stepup.reprep.api.render_jinja]

## [2.0.2][] - 2025-01-22 {: #v2.0.2 }

This is the first release of StepUp RepRep that is compatible with StepUp Core 2.0.0.
(Earlier 2.0 releases were yanked due to packaging issues.)

### Added

- Add `smarty` extension to markdown conversion.
- Add option to insert blank page after odd-paged PDF when concatenating PDFs.

### Changed

- Compatibility with StepUp Core 2.0.0, which breaks compatibility with older StepUp Core versions.

### Fixed

- Use `shlex` for building shell commands in `stepup.reprep.api` to avoid shell injection.

## [1.4.1][] - 2024-09-02 {: #v1.4.1 }

### Added

- An extra argument was added to `convert_markdown` to specify CSS files.
- Support default arguments for `convert_markdown` defined as environment variables:
  `${REPREP_KATEX_MACROS}` and `${REPREP_MARKDOWN_CSS}`.

### Fixed

- Fix bug: put header output of `markdown_katex` plugin in the HTML header.
- Fix bug: rewrite paths to CSS files in `convert_markdown`
  to be relative to the parent of the output HTML file.

## [1.4.0][] - 2024-08-27 {: #v1.4.0 }

### Added

- The unplot script, a sanitized version of [Depix](https://github.com/tovrstra/depix).
  It converts paths from SVG files back into data,
  which can be used to reverse-engineer data sets from plots.

### Changed

- Move `load_module_file` from StepUp Core to `stepup.reprep.render`
  and improve it to facilitate local imports.

## [1.3.0][] - 2024-06-28 {: #v1.3.0 }

### Added

- The script `rr-sync-zenodo` and corresponding StepUp API function `sync_zenodo()`
  synchronize your local data with a draft dataset on Zenodo.
- Small documentation updates

### Fixed

- Upgraded dependency markdown-katex to version 202406.1035
  and enabled concurrency for markdown conversion with equations.
- Scrub PDF files after opening them with `fitz`.
  See <https://github.com/pymupdf/PyMuPDF/issues/3635>

## [1.2.1][] - 2024-05-27 {: #v1.2.1 }

### Changed

- Conversion from HTML to weasyprint is now a two-step process and includes detection
  of implicit input files used in the HTML to PDF conversion. (Images and external CCS)
- Improved reusability of script modules:
  `add_notes_pdf`, `check_hrefs`, `convert_inkscape`, `convert_markdown`,
  `convert_weasyprint`, `latex`, `latex_flat`, `make_inventory`, `normalized_pdf`,
  `nup_pdf`, `raster_pdf`, `render` and `zip_inventory`.

### Fixed

- Fixed a few errors in the HTML generated by `convert_markdown()`

## [1.2.0][] - 2024-05-20 {: #v1.2.0 }

### Added

- `rr-zip-inventory` command to manually create a reproducible ZIP file from an `inventory.txt` file.
- More documentation on how to work with inventory files.
- Tutorial for archiving StepUp publication Git repositories.

### Changed

- Renamed all `MANIFEST` and `manifest` occurrences to `inventory`
  and removed dependency of setuptools for processing such files.
- The API of `make_inventory` is made simpler than that of `make_manifest`.
- The commands supported in `inventory.def` files now differ from those in setuptools:
  `include`, `exclude`, `include-git`, `exclude-git`, `include-workflow` and `exclude-workflow`.
- The css style has been made customizable in `convert_markdown`.
- KaTeX is now optional in `convert_markdown`.

### Fixed

- An error message is raised when trying to a put a directory in an inventory file.
- Symbolic links are no longer dereferenced when they are listed in an inventory file.
- Symbolic links are archived in ZIP files without dereferencing.

## [1.1.2][] - 2024-05-16 {: #v1.1.2 }

### Fixed

- Nicer fix for concurrent Inkscape SVG to PDF or PNG conversion
  (with `SELF_CALL=x`).
  See: <https://gitlab.com/inkscape/inkscape/-/issues/4716>
- Make unit tests work with stepup-core 1.2.2.

## [1.1.1][] - 2024-05-07 {: #v1.1.1 }

### Fixed

- Inkscape SVG to PDF or PNG conversion now works also in parallel,
  thanks to the workaround posted here:
  <https://gitlab.com/inkscape/inkscape/-/issues/4716>
- LibrOffice PDF conversion now works also in parallel,
  thanks to the workaround posted here:
  <https://bugs.documentfoundation.org/show_bug.cgi?id=106134>
- Inkscape conversion no longer opens files in write mode,
  which triggered the watcher of StepUp Core.
- Fixed packaging mistake that confused PyCharm and Pytest.

### Changed

- Documentation improvements

## [1.1.0][] - 2024-05-02 {: #v1.1.0 }

### Changed

- Documentation improvements
- Unit tests are made compatible with StepUp Core 1.2.0.

## [1.0.0][] - 2024-04-25 {: #v1.0.0 }

Initial release

[Unreleased]: https://github.com/reproducible-reporting/stepup-reprep
[2.3.2]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.3.2
[2.3.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.3.1
[2.3.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.3.0
[2.2.3]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.2.3
[2.2.2]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.2.2
[2.2.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.2.1
[2.2.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.2.0
[2.1.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.1.0
[2.0.2]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.0.2
[1.4.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.4.1
[1.4.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.4.0
[1.3.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.3.0
[1.2.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.2.1
[1.2.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.2.0
[1.1.2]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.1.2
[1.1.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.1.1
[1.1.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.1.0
[1.0.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.0.0
