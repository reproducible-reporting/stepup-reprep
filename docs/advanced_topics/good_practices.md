<!-- markdownlint-disable no-duplicate-heading -->

# Good Practices

This tutorial lists some recommendations to facilitate data accuracy, reuse and reproducibility
when working on a StepUp RepRep project.

The [first section](#summaries) contains a compact summary of the recommendations,
and refer to parts of the [second section](#details) for more background
and motivation behind the recommendations.

## Summaries

The summaries below are grouped into categories, and within each category,
there are two classes of recommendations:

- *"Must"* recommendations are highly encouraged.
  Even if you initially neglect some of these recommendations,
  you would benefit from converting your repository to comply with them.
- *"Should"* recommendations are also encouraged but are considered less urgent.
  There may be external factors, such as a publisher, that force you to deviate.

### Filename Conventions

#### Must

- Use semantic file and directory names to organize your data.
- If directory or file names contain numbers,
  zero-pad them so that all relevant information is nicely aligned
  and file names are sorted correctly.

    Good example:

    ```text
    pressure-000.1MPa.txt
    pressure-001.0MPa.txt
    pressure-010.0MPa.txt
    pressure-100.0MPa.txt
    ```

    Bad example:

    ```text
    pressure-0.1MPa.txt
    pressure-100.0MPa.txt
    pressure-10.0MPa.txt
    pressure-1.0MPa.txt
    ```

- Similarly, keywords can be padded with dashes or underscores, for instance:

    ```text
    opt__low
    opt_high
    ```

- If you use a similar structure within multiple directories,
  use exactly the same file names within the directories.
  This facilitates automation.

    Good example:

    ```text
    opt__low/compute.py
    opt_high/compute.py
    ```

    Bad example:

    ```text
    opt__low/compute__low.py
    opt_high/compute_high.py
    ```

    Terrible example:

    ```text
    opt__low/compute.py
    opt_high/calculate.py
    ```

### Tex Sources

#### Must

- All documents are written in LaTeX.
- Any unused LaTeX package is a good package.
- Each sentence starts on a new line in the LaTeX source.
- Use single-column and double-line spacing to make the PDF easier to review.
- Use [BibSane](https://github.com/reproducible-reporting/bibsane) to clean up your BibTeX files.
  Hint: [Quick DOI to BIB conversion](https://www.doi2bib.org)
- Avoid `\subfigure`. Instead, merge panels into one PDF. (See [Tile PDFs](tile_pdfs.md).)

#### Should

- Some packages, such as `todo`, are useful while drafting a manuscript.
  Separate these clearly from other `\usepackage` lines,
  so that they can be easily deleted when the manuscript is finished.
- Define as few custom commands as possible.
- Avoid using low quality publisher article classes.
  (ACS has a decent one.)

### Figures

#### Must

- Separate data generation or collection from actual plotting:
  Perform these two steps in separate Python scripts.
  This means committing the following to Git:

    - Data files (e.g., CSV) containing plot data, including generated data.
      This allows for verification of reproducibility.

    - Scripts that generate the data, if applicable.

    - Scripts that generate the plots using the above data as input.
      Use matplotlib unless otherwise justified.

    - A `README.md` or docstrings summarizing the scripts and data.

- Use Inkscape (>= 1.2) to create drawings and commit SVG source files.

- Use bitmap formats only as an intermediate format
  when vector graphics PDFs show performance problems.
  This is typically the case for plots with many thousands of data points:
  Use high-resolution PNG files (not GIF, JPEG or other formats).

- [Avoid using Jupyter Notebooks](#jupyter-notebooks) as a tool for creating plots.

### Tables

#### Must

Commit the following to the Git history:

- Machine-readable files, such as CSV, containing table data.
- Scripts that generate LaTeX source for the tables.
- A `README.md` or docstrings summarizing the scripts and data.
- [Avoid using Jupyter Notebooks](#jupyter-notebooks) as a tool for creating tables.

### Data Sets

#### Must

- Use `dataset-{name}` directories for data that cannot (easily) be generated from scratch.
  For example:

    - External datasets.
    - Expensive calculations.
    - (Large amounts of) experimental measurements.
    - Data generated with closed-source software.
      (Avoid closed-source software when you have the choice.)
    - Data created with specialized hardware that is not generally available.
    - Manually curated data.

- Add scripts and implementations to regenerate the data,
  integrating them as much as possible with StepUp RepRep.

- Add a `README.md` file that explains:

    - How the data was generated.
    - The software that was used.
    - Directory and file organization.
    - File content details.

- Datasets are Zipped in the end, so store uncompressed data in the repository.

- [Avoid using Jupyter Notebooks](#jupyter-notebooks) as a tool for working with datasets.

- Do not invent your own file formats.

- Do not use tar files, especially compressed ones, due to data loss concerns.
  ZIP is more robust, because each file is compressed individually.

- [Do not use HDF5 files](#hdf5) because of data integrity issues.

- Do not use Python pickle files,
  as they can only be loaded when the corresponding Python packages are available.
  This is too restrictive for long-term data preservation.

- Do not use file formats that can only be used with closed source software.

#### Should

- For files larger than exceed 500 kB, use [Git LFS](https://git-lfs.com/),
  instead of committing them directly into the Git repository.
  The threshold can be increased for convenience,
  but be aware of the storage quota of the remote Git repository.
  For GitHub, the maximum currently appears to be 5 GB (for the entire history).

- When datasets become large for Git LFS,
  collect the data on a remote server that all co-authors can access.
  Check your Git LFS quota to determine a reasonable threshold.
  At the time of writing, this is 2 GB (all files combined) for GitHub.
  If you store data outside of the Git repository,
  clearly document where the data is stored,
  how it can be accessed and who has access permissions.

- For some files, such as zipped collections of data files,
  there is no concern that the zipping itself will be difficult to reproduce,
  so you can add such files to `.gitignore`.

- Do not put compressed files inside compressed files.
  This is usually inefficient and increases the risk of large data losses due to bitrot.

- Avoid binary files in general, as they are harder to reuse in the longer term.

### Software

#### Must

- List software dependencies in `requirements.txt` or `environment.yaml`,
  and pin the version of the requirements to a specific version.
  This allows co-authors to install the same software using `pip` or `conda`.

- If you are using `pip`, prepare a `requirements.in` file
  and convert it using `pip-compile` to a `requirements.txt` file.
  See [pip-tools](https://pypi.org/project/pip-tools/) for more details.

- Use only open source software to (re)build the publication.

- If possible, avoid using closed source software altogether.

- If you do generate some data with closed-source software,
  put it in a `dataset-<name>` directory
  and document in the `README.md` how exactly you generated the data
  and what versions of the software were used.

- If you write your own Python package and use it in a publication,
  make open source releases of all versions used in the paper.
  In addition to `requirements.txt` or `environment.yaml`,
  refer to the source repository and the version of your package in the `README.md`
  of the corresponding `results-<name>` or `dataset-<name>` directories.

    If your Python package is experimental and not yet ready for release,
    include it in the publication project repository under `latest-draft/pkgs/your_package`.
    Add a line `-e latest-draft/pkgs/your_package`
    to the `requirements.txt` and `environment.yaml` files as follows:

    **requirements.txt** (just add a line)

    ```text
    -e latest-draft/pkgs/your_package
    ```

    **environment.yaml** (add a line under the `pip` item)

    ```text
    - pip:
    - '-e latest-draft/pkgs/your_package'
    ```

## Details

This section provides additional background information on the recommendations listed above.
Note that this section is still a work in progress.

### Jupyter Notebooks

Jupyter Notebooks are very popular for interactive Python programming because
you can combine documentation, code, and visualization in one document.
However, Jupyter Notebooks have also been
[criticized for encouraging bad practices](https://doi.org/10.1007/s10664-021-09961-9).
In short, notebooks have inherent limitations that are not easy to overcome:

- Changes to Jupyter Notebooks are not easily visualized with textual diffs.
- Related to the previous point:
  Collaborating on Jupyter Notebooks via version control is problematic.
  Merging different contributions to notebooks easily leads to invalid PYNB files.
- You can execute code cells in notebooks in any order, which can lead to incorrect results.
- You cannot easily import Jupyter Notebooks into other notebooks,
  making them non-modular and monolithic.
  The only way to reuse code from one notebook in another is to copy and paste fragments.

For these reasons, we recommend avoiding them and instead working with reproducible workflows that
combine scripts and analysis tools implemented in Python modules (or packages) and Markdown files.

StepUp addresses the above issues as follows:

- Python source code is implemented in simple Python files,
  so the output `git diff` is readable and merging is relatively easy.
- [StepUp's script protocol](https://reproducible-reporting.github.io/stepup-core/getting_started/script_single)
  allows you to specify the inputs and outputs of each script
  so that StepUp executes them in the correct order.
- If you change one or more scripts, StepUp will determine which scripts need to be re-executed,
  as opposed to manually re-executing cells in notebooks (which is error-prone).
- If you want to create simple reports that integrate your comments, results and figures,
  you can write Markdown files with figures and convert them to PDF using
  [`convert_markdown()`][stepup.reprep.api.convert_markdown]
  and [`convert_weasyprint()`][stepup.reprep.api.convert_weasyprint].

### HDF5

If a process is killed while writing to an HDF5 file,
there is a tiny chance that the entire file will become unreadable,
not just the part that was being written.
Such an abrupt process termination can never be ruled out (e.g., power failure).
We are not aware of any recent fixes for this, e.g.,
some form of [journaling](https://en.wikipedia.org/wiki/Journaling_file_system)
may make the format resilient to interrupted writes.
This happens so rarely that the issue is often dismissed as irrelevant,
see [https://news.ycombinator.com/item?id=10860496](https://news.ycombinator.com/item?id=10860496)

[Zarr](https://zarr.readthedocs.io/en/stable/) is an alternative to HDF5
that has comparable features but does not have the catastrophic data loss issue
because it writes different arrays to different files.
It relies on the robustness of journaling at the file system level,
and so does not need to reimplement it at the file format level.
Zarr does not support some of the extreme performance features of HDF5,
just to say that nothing is perfect.
Still, reliability beats performance, because losing data is a waste of time.

For less demanding applications,
[NumPy's](https://numpy.org/doc/stable/reference/generated/numpy.savez.html) NPY and NPZ
may be a good fit.
Their main advantage is the simplicity and availability within NumPy.

Some online discussions on the subject:

- 2018: [https://forum.hdfgroup.org/t/avoiding-corruption-of-the-hdf5-file/4087](https://forum.hdfgroup.org/t/avoiding-corruption-of-the-hdf5-file/4087)
- 2022: [https://forum.hdfgroup.org/t/corrupted-file-due-to-shutdown/9658](https://forum.hdfgroup.org/t/corrupted-file-due-to-shutdown/9658)
- 2022: [https://janert.me/blog/2022/looking-at-hdf5/](https://janert.me/blog/2022/looking-at-hdf5/)
