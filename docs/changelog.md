<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Effort-based Versioning](https://jacobtomlinson.dev/effver/).
(Changes to features documented as "experimental" will not increment macro and meso version numbers.)

## [Unreleased][]

## [4.0.0rc8][] - 2026-08-26 {: #v4.0.0rc8 }

Compatibility with StepUp Core 4 and a few minor improvements.

(This is release candidate 8 of the upcoming StepUp RepRep 4.0 release.
Note that all changes of the release candidates are combined below.
This section is treated as a draft of the changelog for the final 4.0.0 release,
and will be updated with any further changes before the final release.)

### Added

- Support for `os.PathLike` objects in `stepup.reprep.api` functions.
- An optional `inp` argument in `compile_typst()` to specify additional input files
  on which the typst source may depend.
  If not given, these dependencies are detected automatically after the typst compilation.
  When some of these additional inputs are the outputs of other steps,
  specifying them may improve scheduling efficiency.
- The configuration file of `srr-sync-zenodo` may be written in YAML, JSON or TOML.
  The parser is selected by the suffix of the file name:
  `.yaml` and `.yml`, `.json` or `.toml`.
  YAML remains the recommended format, because it is the only one that supports comments.
  A file named `.zenodo.json` is rejected,
  because that is the metadata Zenodo reads when it archives a GitHub release,
  which follows a different schema.
- A `--dry-run` option in `srr-sync-zenodo`,
  which validates the configuration, resolves the description,
  prints the metadata that would be sent to Zenodo and exits.
  Unlike an unset `REPREP_ZENODO_TOKEN`, this does not depend on the environment.
- Five more custom fields in the `custom_fields` section of the configuration file of
  `srr-sync-zenodo`, which Zenodo deploys as
  `dc:rightsHolder`, `journal:journal`, `meeting:meeting`, `imprint:imprint`
  and `thesis:thesis`.
  They are written as `rights_holder`, `journal`, `meeting`, `imprint` and `thesis`,
  and everything that can be checked without contacting Zenodo is checked locally:
  the ISSN of a journal, the ISBN of an imprint,
  the URL and the identifiers of a meeting,
  and a thesis date that looks like a plain calendar date.
  There is no `creator` custom field,
  because it would repeat `metadata.creators` as free text,
  without ORCIDs or affiliations.

### Changed

- Relicense the StepUp RepRep source code under `LGPL-3.0-or-later`.
  This clarifies that users of StepUp can assign any license of their choice
  to the workflows they create with StepUp (e.g., `plan.py` and related files).
  This has always been the intention, but with this change, it becomes legally explicit.
- Compatibility with StepUp Core 4
- Remove all actions and tools and converted them into standard console scripts,
  all with the `srr-` prefix.
- Refactored `convert_jupyter` to process parameters in the same way as papermill.
- Rename environment variables for consistency:
    - `REPREP_KEEP_TECTONIC_DEPS` -> `REPREP_TECTONIC_KEEP_DEPS`
    - `REPREP_KEEP_TYPST_DEPS` -> `REPREP_TYPST_KEEP_DEPS`
- The Zenodo synchronization has been refactored, including some breaking changes:
    - The `srr-sync-zenodo` command no longer amends input files.
      Instead, all inputs are determined when `sync_zenodo()` is called.
      This has two consequences:
        - The files to upload to Zenodo are no longer listed
          in the `paths` field of the configuration file.
          Instead, they are passed as the second argument of `sync_zenodo()`
          and as positional arguments of `srr-sync-zenodo`, after the configuration file.
          Both entry points reject duplicate file names and more than 100 files,
          which Zenodo does not accept.
        - The description is no longer taken from the `path_readme` field of `sync_zenodo.yaml`.
          Instead, it is passed with the `path_description` argument of `sync_zenodo()`
          and with the `--description` option of `srr-sync-zenodo`.
          (Markdown is converted to HTML automatically.)
    - The token must be specified in the `REPREP_ZENODO_TOKEN` environment variable,
      instead of being specified in the configuration file.
      The old variable `REPREP_PATH_ZENODO_TOKEN` is no longer supported.
      Note that `REPREP_ZENODO_TOKEN` holds the token itself,
      whereas `REPREP_PATH_ZENODO_TOKEN` held the path to a file containing the token.
      When `REPREP_ZENODO_TOKEN` is unset, `srr-sync-zenodo` validates the configuration
      and exits without contacting Zenodo.
      The endpoint stays a field of the configuration file, `endpoint`,
      which is optional and defaults to `https://sandbox.zenodo.org/api`.
      Because StepUp tracks the configuration file,
      switching between the sandbox and the production instance invalidates the step.
    - Unsupported keys in `sync_zenodo.yaml` now raise an error instead of being ignored,
      and values that must be strings are no longer coerced silently.
      For example, an unquoted `version: 1.0` is rejected instead of becoming `"1.0"`.
    - The `code_repository` field of `sync_zenodo.yaml` was replaced by a `custom_fields` section,
      holding the fields with which Zenodo extends the InvenioRDM record.
      It takes `code_repository` and the other fields listed under Added above.
    - Every field that takes an identifier from a controlled vocabulary of Zenodo
      is validated against the identifiers Zenodo has deployed:
      `license`, `resource_type`, `relation_type`,
      `development_status` and `programming_languages`.
      An identifier that Zenodo does not know makes a deposit fail,
      so it is rejected locally instead,
      with an error message naming the vocabulary and its URL.
      Two resource types that `srr-sync-zenodo` used to accept are gone,
      because Zenodo no longer offers them: `audio`, for which `video` is the replacement,
      and `publication-thesis`, for which `publication-dissertation` is.
      The identifiers live in `zenodo_vocabularies.yaml`,
      which is regenerated from the Zenodo API
      by `tools/update_zenodo_vocabularies.py` in the source repository.
    - The fields that Zenodo requires are also required in `sync_zenodo.yaml`,
      and the length bounds that Zenodo enforces are checked locally:
      `metadata.creators` holds at least one creator,
      every creator carries a `family_name`,
      and `metadata.title` counts at least three characters.
    - The `metadata.publisher` field is required.
      It used to be optional, but Zenodo refuses to publish a record without a publisher,
      because it needs one to register a DOI,
      so a missing publisher is now reported before the record is created.
    - The `metadata.version` field may follow any convention,
      as long as it is a non-empty string of at most 191 characters.
      Zenodo stores it as free text and does not order the versions of a dataset by it,
      so `srr-sync-zenodo` only tests it for equality with the versions published on Zenodo.
      It creates a new version on Zenodo when the local version was never published,
      and refuses a version that is already published,
      which is usually a stale checkout or a revert instead of a new release.
      For the same reason, it refuses to synchronize a record
      that is no longer the latest published version of the dataset.
    - When a value in `sync_zenodo.yaml` is rejected,
      the error message now explains what is wrong with it,
      instead of only stating that the value is invalid.
    - Everything that the user has to correct, and every request that Zenodo refuses,
      is reported as a message on standard error, after which `srr-sync-zenodo` exits with code 1.
      It used to re-raise the exception after printing the message,
      so the diagnosis was followed by a traceback,
      which for a rejected config file was a nested exception group of about forty lines,
      most of them pointing into the structuring code that `cattrs` generates.
      Only the errors that this command raises on purpose are reported this way.
      An unexpected error still ends in a traceback, because that is a bug to be reported.
    - The documentation and the example now recommend the names `sync_zenodo.yaml`
      for the configuration file and `zenodo_description.md` for the description,
      instead of `zenodo.yaml` and `zenodo.md`,
      because the old names are easily confused with the legacy `.zenodo.json` file.
      These names are only a convention:
      `srr-sync-zenodo` and `sync_zenodo()` accept any path.
    - The documentation of the Zenodo synchronization is split into two pages:
      a guide, which also explains how the legacy `.zenodo.json` file
      and the two Zenodo APIs relate to each other,
      and a reference of the configuration file, with one section per top level key.
      The `access` section, which decides who can see the record and download its files,
      is documented for the first time.

### Removed

- The `tile_pdf` action has been removed, as it is no longer needed.
  This is easily replaced with a simple typst input.
- The `compile_typst()` function no longer scans the `sysinp` dictionary for `Path` objects
  to automatically mark them as input dependencies.

### Fixed

- In `sync_zenodo.yaml`, a single value written where a list of strings belongs
  is read as a one element list.
  For example, `keywords: coffee` is the same as a list holding one keyword.
  This already worked for `license` and now also works for `keywords`
  and `programming_languages`,
  which were previously split into a list of characters.
  A value that is neither a string nor a list of strings is rejected
  with a message naming the expected type.
- `compile_tectonic()` only scans the `error:` lines of Tectonic's standard error stream
  for missing input files.
  As of Tectonic 0.17, a halted run also dumps the engine transcript to that stream,
  from which paths were picked up that are no files at all.
- `srr-sync-zenodo` reads a record that carries no version on Zenodo,
  instead of failing with a `KeyError`.
  Zenodo does not require a version,
  so a record deposited through its web interface before `srr-sync-zenodo` was adopted
  may well have none.
  Such a record never matches the local version, so a new version is created for it.
- The `--clean` option of `srr-sync-zenodo` removes the drafts
  that Zenodo serves beyond the first page of the records of a user.
  As observed on 2026-08-30, that page holds at most 25 records,
  so the drafts of a user with more records than that were silently left behind.
- `srr-sync-zenodo` no longer fails when it is given no files to upload.
  It declared an empty list of uploads, which Zenodo rejects,
  after it had already created the record,
  so every run left another draft behind without recording its id.
  Note that Zenodo refuses to publish a record without files,
  as observed on the sandbox instance on 2026-08-30.
- `srr-sync-zenodo` keeps the publication date of a record that is already published.
  It sent the date of the build with every metadata update,
  which moved the publication date of a published version to the day of the last build.
  A record that is not published yet is still dated on the day it was last synchronized,
  and a new version still gets the date on which it is created.

## [3.1.11][] - 2026-06-16 {: v3.1.11 }

Switch to typst 0.15 and use its improved dependency tracking in `compile_typst`.

### Changed

- The `compile_typst()` function has improved dependency tracking,
  based on the new JSON deps format of typst 0.15.
  Older versions of typst are no longer supported.

## [3.1.10][] - 2026-04-28 {: v3.1.10 }

This is a minor bugfix release.

### Fixed

- Allow for HTML output files in `compile_typst`.

## [3.1.9][] - 2026-03-22 {: v3.1.9 }

Refactor `wrap_git` to support more flexible specification of inputs and outputs.

### Added

- Support for extra `inp`, `env`, `out`, and `vol` arguments in the `wrap_git` API.
  For example, this allows one to specify that the git command uses a file like `.gitattributes`.
  Changes to this file will then trigger the git command to be re-executed in the next build.

### Changed

- The old `out` argument of `wrap_git` is renamed to `stdout`
  to clarify that it only refers to the stdout of the git command,
  and to allow for other output files to be specified with the new `out` argument.
  Existing `plan.py` files must be updated accordingly.

### Fixed

- Update WeasyPrint dependency to version 68.0 to address a security vulnerability in earlier versions.
  See <https://github.com/advisories/GHSA-983w-rhvv-gwmv>.
- Update nbconvert dependency to version 7.17.0 to address a security vulnerability in earlier versions.
  See <https://cwe.mitre.org/data/definitions/427.html>.

## [3.1.8][] - 2025-12-28 {: v3.1.8 }

Bugfix release

### Changed

- Replace `pybtex` by simpler built-in BibTeX parser in `bibsane` written in Lark.
  This eliminates a external dependencies, in particular `latexcodec`, which caused some issues.
- Only report unused citations in `bibsane`, instead of dropping them.
- Downgrade `cattrs` dependency to facilitate installation.
- Updated reference test outputs for StepUp Core 3.2.

### Fixed

- Gracefully handle missing pagination in `bibsane` when reformatting page ranges.

## [3.1.7][] - 2025-12-20 {: v3.1.7 }

Bugfix release

### Added

- Bibsane can automatically add braces around words in titles that contain uppercase letters,
  to avoid unwanted lowercasing by BibTeX styles.
  This rule applies to titles and journal titles.

### Changed

- Distribute smaller source package.

### Fixed

- Correctly report merged records in bibsane's screen output.
- Fix handling of LaTeX encoding in bibsane
  and abbreviation of journal names with non-ASCII characters.

## [3.1.6][] - 2025-11-21 {: v3.1.6 }

Preliminary Tectonic support and minor fixes.

### Added

- Experimental support for the Tectonic LaTeX engine via the `compile_tectonic()` function.

### Fixes

- Minor cleanups.

## [3.1.5][] - 2025-11-11 {: v3.1.5 }

Update for Typst 0.14, refactored bibsane using pybtex.

### Changed

- Refactor bibsane to use [`pybtex`](https://pybtex.org/)
  instead of [`bibtexparser`](https://bibtexparser.readthedocs.io/en/latest/)
  for reading and writing BibTeX files.
  Several minor issues have been fixed in the process, which result in a small change in behavior.
  Most notably, the indentation style has changed because this is yet not configurable in `pybtex`.
- Rename `wrap_git` action to `wrap-git` for consistency with other StepUp actions.
- Update `compile_typst` to work with Typst 0.14.

## [3.1.4][] - 2025-10-18 {: v3.1.4 }

Improved `sync_zenodo` function.

### Added

- Verbose option for [`sync_zenodo()`][stepup.reprep.api.sync_zenodo]
- Allow overriding `path_token` in [`sync_zenodo()`][stepup.reprep.api.sync_zenodo]
  with the `REPREP_PATH_ZENODO_TOKEN` environment variable.
- Add support for multiple licenses in [`sync_zenodo()`][stepup.reprep.api.sync_zenodo].

### Fixed

- Fix Zenodo draft publication REST API.

## [3.1.3][] - 2025-09-28 {: v3.1.3 }

Minor API improvements.

### Changes

- Add support for other objects than `dict`
  for the `sysinp` argument of [`compile_typst()`][stepup.reprep.api.compile_typst].
- The dictionary passed to the `sysinp` argument of
  [`compile_typst()`][stepup.reprep.api.compile_typst]
  is now sanitized to only contain strings as keys and values.
  Integer, float and path values are converted to strings automatically.
- Add sanity check on the positional argument of
  [`sanitize_bibtex()`][stepup.reprep.api.sanitize_bibtex]
  to ensure that it is a `.bib` file.

## [3.1.2][] - 2025-08-25 {: v3.1.2 }

This is a minor feature release.

### Added

- The function `scan_latex_deps` now has a `amend=True` optional argument.
  If it is used in a workflow, it will by default amend the current step with
  all scanned TeX sources as inputs.

## [3.1.1][] - 2025-06-25 {: v3.1.1 }

Minor improvements (Zenodo synchronization, LaTeX dependencies).

### Added

- Detect dependencies in LaTeX from `includepdf` commands.
- Add `copyright` field to Zenodo metadata.

### Fixed

- Fix minor documentation inaccuracies.

## [3.1.0][] - 2025-06-23 {: v3.1.0 }

More powerful `sync_zenodo` command that uses the Invenio RDM API.

### Changed

- Switch from the official Zenodo API to the Invenio RDM API.
  This is a breaking change, with a new layout of the `zenodo.yaml` configuration file.
  See the [Zenodo synchronization documentation](advanced_topics/sync_zenodo.md) for details.
- Add support for more metadata fields in the `zenodo.yaml` configuration file.
  This includes support for keywords, multiple affiliations, RORs, related identifiers,
  funding information and code repository.
- Add the `--clean` option to `sync_zenodo` to remove all draft uploads from Zenodo.
  (Mainly useful for testing purposes.)
- Human-readable output when the `zenodo.yaml` configuration file contains schema errors.

## [3.0.5][] - 2025-06-22 {: v3.0.5 }

This is a bugfix release.

### Fixed

- Ignore links returned by the Zenodo API that are not strings in `sync_zenodo`.
- Amend a `make_inventory` step with all files in an inventory as inputs.

## [3.0.4][] - 2025-06-21 {: v3.0.4 }

Support for ORCID field in `sync_zenodo`.

### Changed

- Added ORCID field to the author metadata in the `sync_zenodo` configuration file.

## [3.0.3][] - 2025-06-14 {: v3.0.3 }

Replace a few more markdown imports.

## [3.0.2][] - 2025-06-14 {: v3.0.2 }

Small improvements and a wrapper for git commands that depend on the commit id.

### Added

- [`wrap_git()`][stepup.reprep.api.wrap_git] to define shell commands
  (typically `git ...`) that need to be re-executed when the current git branch or commit changes.

### Changed

- Use the `markdown-it-py` package instead of `markdown`
  for more precise and faster markdown rendering.

### Fixed

- Make `flatten_latex()` work with other file extensions.

## [3.0.1][] - 2025-05-31 {: v3.0.1 }

Integration with papermill to execute notebooks, and a few bug fixes.

## Added

- Execution of notebooks with [papermill](https://papermill.readthedocs.io),
  using the [`execute_papermill()`][stepup.reprep.api.execute_papermill] API function.

## Fixed

- Fixed outdated information in the Zenodo synchronization documentation,
  and fixed corresponding outdated code.
- Remove `linear=True` argument when saving a PDF with MuPDF
  because it is no longer supported as of MuPDF 1.26.
  (It was not terribly useful in the first place.)
  For more details, see <https://artifex.com/blog/mupdf-removes-linearisation>.

## [3.0.0][] - 2025-05-11 {: v3.0.0 }

Major release with breaking changes, compatible with StepUp Core 3.

### Changed

- Breaking:
    - Compatibility with StepUp Core 3.
    - Migrated `render_jinja()` to StepUp Core 3.

## [2.3.6][] - 2025-04-24 {: v2.3.6 }

Make `sanitize_bibtex()` work without LaTeX and add support for TOML files in `render_jinja()`.

### Added

- Support for TOML files in `render_jinja()`.

### Changed

- Make [`sanitize_bibtex()`][stepup.reprep.api.sanitize_bibtex] usable without LaTeX.
- New output files in the LaTeX fls file are treated as volatile outputs.

## [2.3.5][] - 2025-03-13 {: v2.3.5 }

Bug fix in `rr-cat-pdf` and simplify journal abbreviation in `rr-bibsane`.
This requires an update the `bibsane.yaml` configuration file.

### Fixed

- The `--insert-blank` opton of `rr-cat-pdf` was always active,
  even when not present on the command line, which is now fixed.
- The `abbreviate_journal` feature of bibsane used to work with a cache file,
  which was a remnant from an older implementation.
  This no longer made much sense (because pyiso4 is fast enough)
  and it cache files may cause non-reproducible behavior.
  (They are both inputs and outputs.)
  For these reasons, the cache feature is replaced by two configuration fields in `bibsane.yaml`:

    - A boolean flag `abbreviate_journals` to enable abbreviations.
    - An optional mapping `custom_abbreviations` with abbreviation overrides
      for when pyiso4 does not give the desired result.

  An external file with abbreviations is no longer needed.
  They are just included in the `bibsane.yaml` file.
  (This also means that old bibsane.yaml config files may need to be updated.)
  See [Sanitizing BibTeX files](advanced_topics/bibsane.md) for more details.

## [2.3.4][] - 2025-03-09 {: #v2.3.4 }

Improved handling of LaTeX fls file and refactored `make_inventory()` function.

### Changed

- The arguments of [`make_inventory()`][stepup.reprep.api.make_inventory] are now variadic.
  Files to be included are passed as positional arguments
  and the last positional argument is the inventory file to be written.
  An optional argument `path_def` can be used to specify an inventory definition file.
- The `include-git` and `exclude-git` commands in an inventory definition now accept arguments,
  which are passed to the `git ls-files` command.
- LaTeX output files inferred from the `.fls` file are filtered in the same ways as input files.
  LaTeX sometimes writes output files to `~/.texlive2023/` which should be ignored by StepUp.

### Fixed

- `rr-flatten-latex` now correctly handles empty tex files.

## [2.3.3][] - 2025-03-03 {: #v2.3.3 }

A few minor improvements related to LaTeX and BibTeX, and parameterized Jupyter notebooks.

### Added

- Improve detection of inputs and (volatile) outputs when compiling a LaTeX document:
    - The `-recorder` option of `latex` is used to identify inputs and outputs more precisely.
    - The manual override `%REPREP input` is replaced by `%REPREP inp`.
    - New manual overrides are supported for (volatile) outputs: `%REPREP out` and `%REPREP vol`.
- Add `nbargs` option to [`convert_jupyter()`][stepup.reprep.api.convert_jupyter],
  to call a notebook with arguments.
  If a `list` or a `dict` is given, the data is convert to JSON.

### Changed

- Add `overwrite` option to [`sanitize_bibtex()`][stepup.reprep.api.sanitize_bibtex],
  to flag that `path_out` refers to an input file to be overwritten,
  instead of trying to track it as an output file.

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
    - [`compile_latex()`][stepup.reprep.api.compile_latex]
      no longer creates an inventory file by default.
      To recover the old behavior, add `inventory=True` to the arguments
      or set the environment variable `REPREP_LATEX_INVENTORY="1"`.
    - [`compile_latex()`][stepup.reprep.api.compile_latex] no longer calls `bibsane`
      when the LaTeX source has a BibTeX bibliography.
      If you want to sanitize the BibTeX file, call [`sanitize_bibtex()`][stepup.reprep.api.sanitize_bibtex]
      after `compile_latex()`.
    - The `paths_variables` argument of `render_jinja()`
      has been replaced by a variadic positional parameter (i.e. `*paths_variables`).
- Other changes
    - Change [`convert_weasyprint()`][stepup.reprep.api.convert_weasyprint]
      to perform the conversion in a single step.
    - Improve handling of arguments and dependencies in
      [`convert_markdown()`][stepup.reprep.api.convert_markdown]
    - `render_jinja()` now accepts JSON and YAML files
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
  You can keep depfiles by setting the environment variable `REPREP_TYPST_KEEP_DEPS="1"`,
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
- Rename API function: `render()` -> `render_jinja()`

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
[4.0.0rc8]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v4.0.0rc8
[3.1.11]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.11
[3.1.10]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.10
[3.1.9]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.9
[3.1.8]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.8
[3.1.7]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.7
[3.1.6]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.6
[3.1.5]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.5
[3.1.4]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.4
[3.1.3]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.3
[3.1.2]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.2
[3.1.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.1
[3.1.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.1.0
[3.0.5]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.0.5
[3.0.4]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.0.4
[3.0.3]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.0.3
[3.0.2]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.0.2
[3.0.1]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.0.1
[3.0.0]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v3.0.0
[2.3.6]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.3.6
[2.3.5]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.3.5
[2.3.4]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.3.4
[2.3.3]: https://github.com/reproducible-reporting/stepup-reprep/releases/tag/v2.3.3
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
