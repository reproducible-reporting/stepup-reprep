# Installation

Requirements:

- [POSIX](https://en.wikipedia.org/wiki/POSIX) operating system: Linux, macOS or WSL. StepUp cannot run natively on Windows.
- [Python](https://www.python.org/) ≥ 3.11
- [Pip](https://pip.pypa.io/)

It is assumed you know how to use [Pip](https://pip.pypa.io/).
We recommend performing the installation in a [Python virtual environment](https://docs.python.org/3/library/venv.html) and activating such environments with [direnv](https://direnv.net/).

The RepRep extension (for reproducible reporting) is installed with:

```bash
pip install stepup-reprep
```

(This will also install `stepup-core`.)
