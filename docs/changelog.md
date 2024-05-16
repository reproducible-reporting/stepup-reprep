# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.2] - 2024-05-16

### Fixed

- Nicer fix for concurrent Inkscape SVG to PDF or PNG conversion
  (with `SELF_CALL=x`).
  See: https://gitlab.com/inkscape/inkscape/-/issues/4716
- Make unit tests work with stepup-core 1.2.2.


## [1.1.1] - 2024-05-07

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


## [1.1.0] - 2024-05-02

### Changed

- Documentation improvements
- Unit tests are made compatible with StepUp Core 1.2.0.

## [1.0.0] - 2024-04-25

Initial release
