# Before You Begin

## Initial Competences

The following competences are required (at a basic level) for this template to be useful.

- Unix
- LaTeX
- Git
- Python

Without these competences, it is still possible to contribute to a publication
created with StepUp RepRep, but it will be difficult to take the lead.

## Required Software and Configuration

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

### Ubuntu

On Ubuntu 22, the required and recommended software can be installed using the following steps:

1. Install the following packages:

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

2. Fira fonts (used for presentations) must be installed manually,
   because they have not been packaged for Ubuntu yet.
   This can be achieved as follows:

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

### Fedora

On Fedora (>= 38), the required and recommended software can be installed using the following command:

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

### Conda or Pip

A new dedicated
[pip](https://pip.pypa.io/en/stable/) or [micromamba](https://mamba.readthedocs.io/)
software environment is created for each publication.
It is up to each co-author to decide which one they prefer:

1. A virtual environment with **pip** can install the dependencies
   with low time, bandwidth and storage overheads.
   A sufficiently recent Python version must already be installed.
2. A **micromamba** environment (the fastest and lightest way to use conda)
   is a bit more powerful than pip.
   In principle, you can use it on a system without (a recent version of) Python.
   It can also install non-Python dependencies.
   The main drawbacks are the time it takes to install, the bandwidth consumed during installation,
   and the amount of disk space used.
   Because the cookiecutter requires Python >= 3.7, you already need a working Python version
   before installing micromamba.

The aim is to isolate this software environment from your operating system as much as possible.
This may be hampered by your local configuration, for example:

- Another always-on pip environment (activated in your shell profile, like `.bashrc`)
  may not work well when pip is used for the publication.

- Similarly, another always-on conda environment (activated in your shell profile)
  may not work well when micromamba is used for the publication.

- Using pip for the publication on top of your default conda can work well.
  (Needs more testing.)
