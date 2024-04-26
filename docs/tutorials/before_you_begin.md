# Before you begin

## Initial competences

The following competences are required (at a basic level) for this template to be useful.

- Unix
- LaTeX
- Git
- Python

Without these competences, it is still possible to contribute to a publication
created with StepUp RepRep, but it will be difficult to take the lead.


## Required software and configuration

It is assumed that you have installed and configured the following software,
ideally using your operating system's software installation tool
(app store, package manager, pip, ...).

- Required:
    - [Python](https://www.python.org/) >= 3.11
    - [Git](https://git-scm.com/)
    - [Git LFS](https://git-lfs.com/)
    - [The cookiecutter](https://www.cookiecutter.io/)
      (Only needed to initialize a new publication.)
- Recommended:
    - [Inkscape](https://inkscape.org/) >= 1.2
      (Only needed when the source contains SVG files.
      [It must be executable as `inkscape` on the command-line](https://stackoverflow.com/a/22085247/494584).)
    - `mutool` from [MuPDF](https://mupdf.com/)
    - [TexLive](https://tug.org/texlive/) >= 2022
    - [direnv](https://direnv.net/)
    - A Text editor compatible with [editorconfig](https://editorconfig.org/)

Installation instructions for ...

- ... Ubuntu 22:

    ```bash
    sudo apt install \
      python3.11 \
      python3.11-venv \
      python3-pip \
      python3-cookiecutter \
      inkscape \
      texlive-full \
      git \
      git-lfs \
      direnv \
      mupdf-tools \
      libreoffice
    ```

    Fira fonts (used for presentations) must be installed manually:

    ```bash
    mkdir -p ~/.local/share/fonts
    cd ~/.local/share/fonts
    wget 'https://github.com/firamath/firamath/releases/download/v0.3.4/firamath.tds.zip'
    unzip -j firamath.tds.zip fonts/opentype/public/firamath/FiraMath-Regular.otf
    rm firamath.tds.zip
    cd
    ```

    ```bash
    mkdir -p ~/.local/share/fonts
    cd ~/.local/share/fonts
    wget 'https://github.com/mozilla/Fira/archive/refs/tags/4.202.zip'
    unzip -j 4.202.zip Fira-4.202/otf/*.otf
    chmod -x *.otf
    rm 4.202.zip
    cd
    ```

- ... Fedora:

    ```bash
    sudo dnf install \
      python \
      python3-pip \
      python3-virtualenv \
      python3-cookiecutter \
      inkscape \
      texlive-scheme-full \
      git \
      git-lfs \
      direnv \
      mupdf \
      libreoffice \
      mozilla-fira* \
      texlive-fira*
    ```

A new dedicated
[pip](https://pip.pypa.io/en/stable/) or [micromamba](https://mamba.readthedocs.io/)
software environment is created for each publication.
It is up to each co-author which of the two they prefer:

1. A virtual environment with **pip** can install the dependencies
   with low time, bandwidth and storage overheads.
   You must already have a sufficiently recent Python version installed.
2. A **micromamba** environment (the fastest and lightest way of using conda)
   is a bit more powerful than pip.
   In principle, you can use it on a system without (a recent version of) Python.
   It can also install non-Python dependencies.
   The main disadvantage is the time to install it, consumed bandwidth during the installation, and the high disk usage.
   Also, the cookiecutter requires Python >= 3.7 to work, so you will need Python when
   initializing a new publication from the template.

The goal is to isolate this software environment from your operating system as much as possible.
This may be hampered by your local configuration, e.g.:

- Another always-on pip environment (activated in your shell profile, like `.bashrc`)
  may not work well when pip is used for the publication.

- Similarly, another always-on conda environment (activated in your shell profile)
  may not work well when micromamba is used for the publication.

- Using pip for the publication, on top of your default conda can work well.
  (Needs more testing.)
