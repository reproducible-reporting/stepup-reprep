# Create or clone a project

Follow route **1a + 2** OR route **1b + 2**.

## 0) First-time Git users

If you have not used Git before, you probably haven't configured it yet.
At least run the following (with correct name and email):

```bash
git config --global init.defaultBranch main
git config --global user.name "Your Name"
git config --global user.email Your.Name@email.com
git config --global core.editor nano
```

Also, go through a [Git Tutorial](https://www.w3schools.com/git/default.asp?remote=github) to become familiar with the basic concepts.

## 1a) Start a new publication

- Start a new publication with the [cookiecutter](https://github.com/cookiecutter/cookiecutter):

    ```bash
    cookiecutter https://github.com/reproducible-reporting/templates
    ```

    Follow the instructions on the terminal. You will have to enter:

    - `slug`:
      This a short name for the directory name containing all the sources and compiled outputs.
      Use lower-case characters, digits and hyphens only.
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

    where `'slug'` should be replaced with the directory created by the cookiecutter.

- Before making a first commit, define the software requirements,
  e.g. for post-processing and plotting, in `requirements.txt` **AND** `environment.yaml`.
  If you must use micromamba (e.g. non-Python dependencies), then you can remove `requirements.txt`
  and `setup-venv-pip.sh`.

- Now you can add all the files, commit them, define a remote URL and push the initial contents online:

    ```bash
    git add .
    git commit -a -m "Initial commit"
    git remote add origin 'remote url'
    git push origin main -u
    ```

    where you replace `'remote url'` by the correct one.
    This depends on which online service is used to share the Git repository with your co-authors.
    If in doubt, create a private repository on GitHub.


## 1b) Clone an existing publication

You need a `'remote url'` of an existing publication, which one of your co-authors created.
Substitute this `'remote url'` in the following command, which should be executed in the terminal:

```bash
git clone 'remote url'
cd 'slug'
```

where `'slug'` should be replaced with the directory created by `git clone`


## 2) Set up the software environment

(It is assumed your current working directory is the `'slug'`
defined in the previous section **1a** or **1b**.)

- Install the software environment, using **ONE of the following** commands (**NOT more than one**):

    ```bash
    # Fedora
    ./setup-venv-pip.sh
    ```

    or

    ```bash
    # Ubuntu 22
    PYTHON3=/usr/bin/python3.11 ./setup-venv-pip.sh
    ```

    or

    ```bash
    # Any
    ./setup-venv-micromamba.sh
    ```

- Activate your software environment:

    ```bash
    source .envrc
    ```

    This activation is needed whenever you open a new terminal.
    It is not recommended to add publications-specific activation scripts to your `~/.bashrc`.
    If you find it too tedious to call the activation script over and over again,
    give [`direnv`](https://github.com/direnv/direnv) a try.
    Once `direnv` is installed and configured in your shell profile,
    you only need to allow it once with `direnv allow .`,
    and the `.envrc` script is automatically sourced
    when you change to the directory of the Git repository.

- Install `pre-commit` and `git-lfs` into the new repository:

    ```bash
    pre-commit install
    git-lfs install
    ```

    This is needed whenever your create or clone a Git repository.
    (Normally, that is only once per publication.)

- Now you should be able to build the template manuscript and related documents
  with StepUp RepRep as follows:

    ```bash
    cd latest-draft
    stepup -n
    ```
