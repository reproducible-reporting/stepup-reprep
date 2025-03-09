# Developer Notes

If you would like to contribute, please read [CONTRIBUTING.md](https://github.com/reproducible-reporting/.github/blob/main/CONTRIBUTING.md).

## Development environment

If you break your development environment, you can discard it
by running `git clean -dfX` and repeating the instructions below.

First, create a [StepUp Core development installation](https://reproducible-reporting.github.io/stepup-core/development/).
The following commands assume you create `stepup-core` and `step-reprep` source trees
as subdirectories of the same parent.

Clone the StepUp RepRep repository and create a virtual environment using the following commands

```bash
git clone git@github.com:reproducible-reporting/stepup-reprep.git
cd stepup-reprep
pre-commit install
python -m venv venv
```

Put the following two lines in `.envrc`:

```bash
source venv/bin/activate
export XDG_CACHE_HOME="${VIRTUAL_ENV}/cache"
export STEPUP_DEBUG="1"
export STEPUP_SYNC_RPC_TIMEOUT="30"
```

Finally, run the following commands:

```bash
direnv allow
pip install -U pip
pip install -e .[dev]
pip install -e ../stepup-core[dev] --config-settings editable_mode=strict  # optional
```

## Tests

We use pytest, so you can run the tests as follows:

```bash
pytest -vv
```

## Documentation

The documentation is created with [MkDocs](https://www.mkdocs.org/).

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
