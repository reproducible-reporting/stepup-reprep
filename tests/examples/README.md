<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: LGPL-3.0-or-later
-->

# Examples

The examples follow the conventions of StepUp Core,
see <https://github.com/reproducible-reporting/stepup-core/blob/main/tests/examples/README.md>.
These include the rules for scripts that must also run on Windows.

## External Programs

An example that needs a program other than Python,
such as TeX Live, Tectonic, Typst, Inkscape, `mutool` or LibreOffice,
is skipped when that program is missing,
or when its version differs from the one for which the expected outputs were made.
The example `convert_weasyprint` is skipped when WeasyPrint cannot load its libraries,
which is the case on Windows without GTK.

To run the Typst and Tectonic examples on Windows,
follow [Tests on Windows](../../docs/development.md#tests-on-windows).
