<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: LGPL-3.0-or-later
-->
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Guidance that applies to only part of the repo lives next to the code it governs:

- `tests/CLAUDE.md`: test layout and regenerating expected outputs.

## Project Overview

StepUp RepRep is a [StepUp Core](https://github.com/reproducible-reporting/stepup-core)
extension for reproducible scientific reporting. It wraps external tools (LaTeX, Tectonic,
Typst, Inkscape, WeasyPrint, Papermill, etc.) as StepUp build steps with proper dependency
tracking.

## Architecture

The package is organized around two layers:

- **`stepup/reprep/api.py`** is the Python API that users call in their `plan.py` build
  scripts. Each function creates a StepUp `run(...)` step that registers the
  work to be done, including inputs, outputs, and the action to execute.

- **Individual action modules** (e.g., `compile_latex.py`, `compile_tectonic.py`, etc.)
  each implement a `main()` function that serves as a CLI tool.
  These are registered via `[project.scripts]` in `pyproject.toml` (e.g., `srr-compile-latex`)
  and invoked by StepUp steps as external commands.

## Development Setup

```bash
uv sync --extra dev
pre-commit install
```

The `.envrc` activates the venv and sets useful env vars (`STEPUP_DEBUG=1`, etc.) for
`direnv`. Alternatively prefix commands with `uv run`.

## Coding Conventions

- **En and em dashes** never appear in prose (comments, docstrings, Markdown), in neither
  glyph (–, —) nor ASCII (--) form. Use "which"/"because"/"that", or split the sentence.
- **Data classes use `attrs`** (`@attrs.define`, `frozen=True` for value objects), not
  `dataclasses`, `NamedTuple`, or a hand-written `__init__`.
- **Do not add `# noqa`** unless the violation is a genuine false positive that cannot be
  resolved by restructuring.
