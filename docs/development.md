---
description: >-
  Set up a StepUp RepRep development environment with uv, direnv and pre-commit,
  and find out how to run the tests, build the documentation and make a release.
---

<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Developer Notes

If you would like to contribute, please read [CONTRIBUTING.md](https://github.com/reproducible-reporting/.github/blob/main/CONTRIBUTING.md).

## Development environment

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

The documentation is created with [MkDocs](https://www.mkdocs.org/).
Only the current version is published:
every commit on the main branch republishes the site with GitHub Pages.

Edit the documentation markdown files with a live preview by running:

```bash
mkdocs serve
```

(Keep this running.)
Then open the live preview in your browser: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
and edit Markdown files in your IDE.

Please, use [Semantic Line Breaks](https://sembr.org/)
because it results in cleaner file diffs when editing documentation.

## How to Make a Release

- Mark the release in `changelog.md`.
- Make a new commit and tag it with `vX.Y.Z`.
- Trigger the PyPI GitHub Action: `git push origin main --tags`.
