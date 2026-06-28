# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StepUp RepRep is a [StepUp Core](https://github.com/reproducible-reporting/stepup-core)
extension for reproducible scientific reporting. It wraps external tools (LaTeX, Tectonic,
Typst, Inkscape, WeasyPrint, Papermill, etc.) as StepUp build steps with proper dependency
tracking.

**Current state:** The `refactor4` branch is upgrading RepRep to work with StepUp Core
v4 (rc1). Many details in the existing code reflect StepUp 3 conventions that will change
during this refactor.

## Architecture

The package is organized around two layers:

- **`stepup/reprep/api.py`** — Python API that users call in their `plan.py` build
  scripts. Each function creates a StepUp `run(...)` step that registers the
  work to be done, including inputs, outputs, and the action to execute.

- **Individual action modules** (e.g., `compile_latex.py`, `compile_tectonic.py`, etc.) —
  Each module implements a `main()` function that serves as a CLI tool.
  These are registered via `[project.scripts]` in `pyproject.toml` (e.g., `srr-compile-latex`)
  and invoked by StepUp steps as external commands.

Key supporting modules:

- `inventory.py` / `make_inventory.py` / `check_inventory.py` / `zip_inventory.py` — file
  inventory creation, verification, and packaging
- `bibparser.py` / `bibsane.py` — BibTeX parsing and sanitization using a Lark grammar
  (`bibtex.lark`)
- `latex_deps.py` / `latex_log.py` / `flatten_latex.py` — LaTeX dependency scanning and
  log parsing
- `pytest.py` — test helpers, wraps `stepup.core.pytest.run_example` with an added
  reproducibility check

## Development Setup

```bash
uv sync --extra dev
pre-commit install
```

The `.envrc` activates the venv and sets useful env vars (`STEPUP_DEBUG=1`, etc.) for
`direnv`. Alternatively prefix commands with `uv run`.

## Commands

```bash
# Run tests (parallel by default, excludes heavy tests)
pytest -vv

# Run a single test
pytest -vv tests/test_bibparser.py

# Run a specific example test
pytest -vv tests/test_examples.py::test_example[convert_markdown]

# Lint
ruff check stepup/ tests/
ruff format --check stepup/ tests/

# Docs live preview
mkdocs serve
```

To regenerate expected outputs for example tests:

```bash
STEPUP_OVERWRITE_EXPECTED=1 pytest -vv tests/test_examples.py
```

## Testing

- Unit tests live in `tests/test_*.py`; integration tests are in `tests/examples/` and run
  via `tests/test_examples.py`
- Example tests copy a fixture directory to a temp dir, run StepUp, then compare outputs
  against `expected/` subdirectories
- Tests marked `heavy` are skipped in CI; LaTeX/Tectonic/Inkscape/Typst/Jupyter tests are
  skipped when the respective tool is absent
- `pytest.ini_options` sets `-n auto --dist worksteal` (parallel) and `--strict-markers`

## Linting

- Ruff is configured in `pyproject.toml` with `line-length = 100`,
  `target-version = "py311"`, and a broad rule set
- Pre-commit runs ruff, markdownlint, and other checks automatically on commit
