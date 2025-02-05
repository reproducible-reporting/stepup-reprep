# Installation

!!! warning "The installation instructions are listed here for completeness."

    If you are new to StepUp RepRep, we recommend that you follow the
    [Template Tutorial](from_template/introduction.md) instead.
    One of the steps in that tutorial is to install StepUp RepRep in a suitable virtual environment.

## Requirements

- [POSIX](https://en.wikipedia.org/wiki/POSIX) operating system: Linux, macOS or WSL.
  StepUp cannot run natively on Windows.
- [Python](https://www.python.org/) ≥ 3.11
- [Pip](https://pip.pypa.io/)

It is assumed you know how to use [Pip](https://pip.pypa.io/).
We recommend performing the installation in a
[Python virtual environment](https://docs.python.org/3/library/venv.html)
and activating such environments with [direnv](https://direnv.net/).

## Minimal installation

The RepRep extension (for reproducible reporting) is installed with:

```bash
pip install stepup-reprep
```

(This will also install [StepUp Core](https://reproducible-reporting.github.io/stepup-core/).)
