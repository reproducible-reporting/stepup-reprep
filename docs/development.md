---
description: >-
  Set up a StepUp RepRep development environment with uv, direnv and pre-commit,
  and find out how to run the tests, build the documentation and make a release.
---

<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Developer Guide

If you would like to contribute, please read [CONTRIBUTING.md](https://github.com/reproducible-reporting/.github/blob/main/CONTRIBUTING.md).

## Development Environment

If you break your development environment, you can discard it
by running `git clean -dfX` in the project root and repeating the instructions below.

We use [uv](https://docs.astral.sh/uv/) to manage the development environment.
Install it by following the [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

A local installation for testing and development can be set up
using the following commands:

```bash
git clone git@github.com:reproducible-reporting/stepup-reprep.git
cd stepup-reprep
uv sync --extra dev
pre-commit install
```

Put the following two lines in `.envrc`:

```bash
source .venv/bin/activate
export XDG_CACHE_HOME="${VIRTUAL_ENV}/cache"
export STEPUP_DEBUG="1"
export STEPUP_BUILD_DURATION="0"
export STEPUP_SYNC_RPC_TIMEOUT="30"
```

Finally, run the following commands:

```bash
direnv allow
```

Alternatively, you can prefix commands with `uv run` (e.g. `uv run pytest`)
instead of activating the virtual environment.

Note that `uv.lock` is not committed to the repo.
For development and CI, the latest versions of dependencies are used instead of some locked versions.

## Tests

We use pytest, so you can run the tests as follows:

```bash
pytest -vv
```

### Tests on Windows

The test suite also runs on Windows.
The examples that need a program which is not installed are skipped,
see `tests/examples/README.md`.

The examples that use Typst and Tectonic need two settings on Windows:

- Typst 0.15 and Tectonic 0.17 must be on the `PATH`.
- `FONTCONFIG_FILE` must name a fontconfig configuration.
  Without it, Tectonic prints `Fontconfig error: Cannot load default config file`
  to the standard error on every run, as observed with Tectonic 0.17 on Windows.
  The Tectonic examples then fail, because their expected output has no standard error.
  A configuration that only lists the fonts of Windows suffices,
  such as `tools/fonts.conf` in this repository.

The workflow `.github/workflows/pytest.yaml` makes both settings on the Windows runners of GitHub.
The PowerShell script `tools/winvm-tools.ps1` makes both settings for the whole machine,
for which it needs to run as administrator.
It was written for the Windows test VM of StepUp Core,
which `tools/winvm/winvm.sh` in the
[StepUp Core repository](https://github.com/reproducible-reporting/stepup-core/blob/main/tools/winvm/README.md)
manages.
With a checkout of StepUp Core next to this repository and an existing VM,
install the programs once and run the tests as follows:

```bash
W=../stepup-core/tools/winvm/winvm.sh
$W start
$W sync
$W run "powershell -ExecutionPolicy Bypass -File tools\winvm-tools.ps1"
$W test
$W stop
```

## Documentation

The documentation is created using [Zensical](https://zensical.org/),
configured in `zensical.toml`.
Only the current version is published:
every commit on the main branch republishes the site with GitHub Pages.

Edit the documentation Markdown files with a live preview by running:

```bash
zensical serve
```

(Keep this running.)
Then open the live preview in your browser at
[http://localhost:8000/stepup-reprep/](http://localhost:8000/stepup-reprep/)
and edit Markdown files in your IDE.

Pages that walk through an example include its sources and outputs
with the block form of the [Snippets](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/)
extension, using paths relative to `docs/`:

<!-- The leading semicolons escape the snippet markers and do not appear on the page. -->

````markdown
```python
;--8<--
advanced_topics/unplot/plan.py
;--8<--
```
````

Do not use the single-line form `--8<-- "path"` in a Python code block,
because Ruff formats the code blocks in Markdown files and rewrites that line
as if it were a Python expression.
The block form is not valid Python, so Ruff leaves it alone.

Please use [Semantic Line Breaks](https://sembr.org/)
because it results in cleaner file diffs when editing documentation.

## How to Make a Release

- Mark the release in `changelog.md`.
- Make a new commit and tag it with `vX.Y.Z`.
- Trigger the PyPI GitHub Action: `git push origin main --tags`.
