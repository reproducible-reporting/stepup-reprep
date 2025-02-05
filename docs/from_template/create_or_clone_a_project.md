# Create or Clone a Project

Follow route **1a + 2** OR route **1b + 2**.

## 0) First-time Git Users

If you have not used Git before, you probably haven't configured it yet.
At least run the following (with correct name and email):

```bash
git config --global init.defaultBranch main
git config --global user.name "Your Name"
git config --global user.email "Your.Name@email.com"
git config --global core.editor nano
```

Also, go through a [Git Tutorial](https://www.w3schools.com/git/default.asp?remote=github)
to become familiar with the basic concepts.

## 1a) Start a New Publication

- Start a new publication using the [cookiecutter](https://github.com/cookiecutter/cookiecutter):

    ```bash
    cookiecutter https://github.com/reproducible-reporting/templates
    ```

    Follow the instructions on the terminal.
    You will need to enter:

    - `slug`:
      This is a short name for the directory containing all sources and compiled outputs.
      Use only lower-case characters, digits and hyphens.
    - `article`:
      The LaTeX article template you want to use.
    - `supp`:
      The LaTeX supporting of supplementary information template you want to use.
    - `cover`:
      The LaTeX template for the cover letter.

- Enter the newly created directory (`slug`) and initialize the Git repository

    ```bash
    cd 'slug'
    git init
    ```

    Replace `'slug'` with the directory created by the cookiecutter.

- Before making a first commit, define the software requirements,
  e.g., for post-processing and plotting, in `requirements.in` and/or `environment.yaml`.
  Pin versions of your dependencies with `==X.Y.Z` as shown in the example files in the template.

    - If you must use micromamba, because you have non-Python dependencies,
      you can remove `requirements.in`  and `setup-venv-pip.sh`.
    - If you prefer to create a *pure Python* project,
      you can remove `environment.yaml` and `setup-venv-micromamba.sh`.

    Note that the Python environment uses [pip-tools](https://github.com/jazzband/pip-tools)
    to manage dependencies.
    This facilitates reproducibility because the results of the package dependency calculation
    are stored in `requirements.txt` and this file is also committed to the Git repository

- Now you can add all the files, commit them, define a remote URL and push the initial contents online:

    ```bash
    git add .
    git commit -a -m "Initial commit"
    git remote add origin 'remote url'
    git push origin main -u
    ```

    Replace `'remote url'` with the correct one.
    This depends on which online service is used to share the Git repository with your co-authors.
    If in doubt, create a private repository on GitHub.

## 1b) Clone an Existing Publication

You need a `'remote url'` of an existing publication, which one of your co-authors created.
Substitute this `'remote url'` in the following command, which should be executed in the terminal:

```bash
git clone 'remote url'
cd 'slug'
```

Replace `'slug'` with the directory created by `git clone`.

## 2) Set Up the Software Environment

(It is assumed that your current working directory is the `'slug'`
defined in the previous section **1a** or **1b**.)

- Install the software environment, using **ONE of the following** commands (**NOT more than one**):

    - Fedora or Ubuntu 24:

        ```bash
        ./setup-venv-pip.sh
        ```

    - Ubuntu 22

        ```bash
        PYTHON3=python3.11 ./setup-venv-pip.sh
        ```

    - Any OS but requires more resources

        ```bash
        ./setup-venv-micromamba.sh
        ```

- Activate your software environment:

    ```bash
    source .envrc
    ```

    This activation is required each time you open a new terminal.
    It is not recommended to add publication-specific activation scripts to your `~/.bashrc`.
    If you find it too tedious to run the activation script over and over again,
    try using [`direnv`](https://github.com/direnv/direnv).
    Once `direnv` is installed and configured in your shell profile,
    you only need to allow it once with `direnv allow .`,
    and the `.envrc` script is automatically sourced
    when you change to the directory of the Git repository.

- Install `pre-commit` and `git-lfs` into the new repository:

    ```bash
    pre-commit install
    git-lfs install
    ```

    This is needed each time you create or clone a Git repository.
    Normally, that is only once per publication.

- You should now be able to build the template manuscript and related documents
  with StepUp RepRep as follows:

    ```bash
    cd latest-draft
    stepup -n
    ```
