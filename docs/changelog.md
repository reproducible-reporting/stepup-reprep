# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Add `smarty` extension to markdown conversion.

## [1.4.1] - 2024-09-02 {: #v1.4.1 }

### Added

- An extra argument was added to `convert_markdown` to specify CSS files.
- Support default arguments for `convert_markdown` defined as environment variables:
  `${REPREP_KATEX_MACROS}` and `${REPREP_MARKDOWN_CSS}`.

### Fixed

- Fix bug: put header output of `markdown_katex` plugin in the HTML header.
- Fix bug: rewrite paths to CSS files in `convert_markdown`
  to be relative to the parent of the output HTML file.


## [1.4.0] - 2024-08-27 {: #v1.4.0 }

### Added

- The unplot script, a sanitized version of [Depix](https://github.com/tovrstra/depix).
  It converts paths from SVG files back into data,
  which can be used to reverse-engineer data sets from plots.

### Changed

- Move `load_module_file` from StepUp Core to `stepup.reprep.render`
  and improve it to facilitate local imports.


## [1.3.0] - 2024-06-28 {: #v1.3.0 }

### Added

- The script `reprep-sync-zenodo` and corresponding StepUp API function `sync_zenodo()`
  synchronize your local data with a draft dataset on Zenodo.
- Small documentation updates

### Fixed

- Upgraded dependency markdown-katex to version 202406.1035
  and enabled concurrency for markdown conversion with equations.
- Scrub PDF files after opening them with `fitz`.
  See https://github.com/pymupdf/PyMuPDF/issues/3635


## [1.2.1] - 2024-05-27 {: #v1.2.1 }

### Changed

- Conversion from HTML to weasyprint is now a two-step process and includes detection
  of implicit input files used in the HTML to PDF conversion. (Images and exteral CCS)
- Improved reusability of script modules:
  `add_notes_pdf`, `check_hrefs`, `convert_inkscape`, `convert_markdown`,
  `convert_weasyprint`, `latex`, `latex_flat`, `make_inventory`, `normalized_pdf`,
  `nup_pdf`, `raster_pdf`, `render` and `zip_inventory`.

### Fixed

- Fixed a few errors in the HTML generated by `convert_markdown()`


## [1.2.0] - 2024-05-20 {: #v1.2.0 }

### Added

- `reprep-zip-inventory` command to manually create a reproducible ZIP file from an `inventory.txt` file.
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


## [1.1.2] - 2024-05-16 {: #v1.1.2 }

### Fixed

- Nicer fix for concurrent Inkscape SVG to PDF or PNG conversion
  (with `SELF_CALL=x`).
  See: https://gitlab.com/inkscape/inkscape/-/issues/4716
- Make unit tests work with stepup-core 1.2.2.


## [1.1.1] - 2024-05-07 {: #v1.1.1 }

### Fixed

- Inkscape SVG to PDF or PNG conversion now works also in parallel,
  thanks to the workaround posted here:
  https://gitlab.com/inkscape/inkscape/-/issues/4716
- Libroffice PDF conversion now works also in parallel,
  thanks to the workaround posted here:
  https://bugs.documentfoundation.org/show_bug.cgi?id=106134
- Inkscape conversion no longer opens files in write mode,
  which triggered the watcher of StepUp Core.
- Fixed packaging mistake that confused PyCharm and Pytest.

### Changed

- Documentation improvements


## [1.1.0] - 2024-05-02 {: #v1.1.0 }

### Changed

- Documentation improvements
- Unit tests are made compatible with StepUp Core 1.2.0.

## [1.0.0] - 2024-04-25 {: #v1.0.0 }

Initial release


[Unreleased]: https://github.com/reproducible-reporting/stepup-reprep
[1.4.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.4.1
[1.4.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.4.0
[1.3.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.3.0
[1.2.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.2.1
[1.2.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.2.0
[1.1.2]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.1.2
[1.1.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.1.1
[1.1.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.1.0
[1.0.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v1.0.0
