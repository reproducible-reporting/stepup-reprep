# Template conventions

This tutorial lists some recommendations that facilitate data reuse and reproducibility.


## General filename conventions

### Must

- Use semantic file and directory names to organize your data.
- When directory or file names contain numbers, zero-pad them,
  so all relevant information is nicely aligned and filenames are correctly
  sorted.

    Good example:
    ```
    pressure-000.1MPa.txt
    pressure-001.0MPa.txt
    pressure-010.0MPa.txt
    pressure-100.0MPa.txt
    ```

    Bad example:
    ```
    pressure-0.1MPa.txt
    pressure-100.0MPa.txt
    pressure-10.0MPa.txt
    pressure-1.0MPa.txt
    ```

- Similarly, keywords can be padded with dashes or undersores, e.g.
  ```
  opt__low
  opt_high
  ```

- When using a similar structure inside multiple directories, use
  exactly the same filenames within the directories.
  This is facilitates automation.

    Good example:
    ```
    opt__low/compute.py
    opt_high/compute.py
    ```

    Bad example:
    ```
    opt__low/compute__low.py
    opt_high/compute_high.py
    ```

    Terrible example:
    ```
    opt__low/compute.py
    opt_high/calculate.py
    ```


## Tex sources

### Must

- All documents are written in LaTeX.
- Every LaTeX package you don't use, is a good package.
- Every sentence starts on a new line in the LaTeX source.
- To facilitate reviewing the PDF, use single-column and double line spacing.
- Use [BibSane](https://github.com/reproducible-reporting/bibsane) to keep your BibTeX files sane.
- Hint: [Quick DOI tot BIB conversion](https://www.doi2bib.org)

### Should

- Some pakcages, like `todo` are convenient while writing.
  Clearly separate these from other `\usepackage` lines, so they can be easily deleted
  when finalizing the manuscript.
- Define as little commands as possible.
- Avoid low-quality publisher article classes. (ACS has a decent one.)
- Avoid `\subfigure`. Merge panels into one PDF instead. (See [Tiling PDFs](tiling_pdfs.md).)


## Figures

### Must

- Separate the data generation or collection from the actual plotting.
  (Do these in two separate Python scripts.)
  This means you commit the following to Git:
    - Data files containing the data shown in the plots.
      Text files like CSV are preferred when possible.
      Also commit these files when the data is auto-generated.
      This may not seems useful, but it allows for verification of reproducibility.
    - Scripts that generate data, if applicable.
    - Scripts to generate the plot, using the above data as input.
      Use matplotlib unless you have good reasons not to.
    - A `README.md` or docstrings summarizing the scripts and the data.
- When making drawings, use Inkscape (>= 1.2) and commit the SVG source files.
- Use bitmap formats only as an intermediate format when the vector graphics PDF show performance issues.
  This typically happens when a plot contains many thousands of data points.
  Use high-resolution PNG files (not GIF, JPEG or any other format).

### Avoid

- Jupyter notebooks

## Tables

### Must

Commit the following:

- Machine-readable files containing the data shown in the table, e.g. CSV.
- Scripts to generate the LaTeX source of table.
- A `README.md` or docstrings summarizing the scripts and the data.

### Avoid

- Jupyter notebooks


## Data sets

### Must

- The `dataset-{name}` directories are appropriate when
  the data cannot be regenerated from scratch,
  or when it would be impractical to do so on a routine basis:

    - External data sets.
    - Expensive calculations that you carried out separately.
    - Data generated with closed-source software.
      (Avoid closed-source software when you have the choice.)
    - Data generated with specialized hardware not generally available.
    - Manually curated data.

- Add as many scripts and implementations as possible to regenerate the data.
  Integrate these scripts as much as possible with StepUp RepRep.

- Add a `README.md` file explaining the following:

    - How the data were generated
    - Software that was used
    - Directory and file organization
    - File content details

- Data sets are Zipped in the end, so store uncompressed data in the repository.

### Should

- When data sets become large for Git (more than 500 kB), use [Git LFS](https://git-lfs.com/).
  The threshold can be increased for convenience,
  but keep in mind that most remote Git repositories have storage quota.
  For GitHub, the maximum seems to be 5 GB at the moment (for the entire history).
- When data sets become large for Git LFS (more than 50 MB), use University-provided storage.
  Check your Git LFS quota to define a sensible threshold.
  At the time of writing, this is 2 GB (all files combined) for GitHub.
  When offloading data outside the Git repository,
  document clearly where the data is stored, how to access and who has access permissions.
- For some files, e.g. a zipped collection of data files,
  there are no concerns that the zipping itself is difficult to reproduce,
  so you can decide not to store the zip file separately and to add it to `.gitignore` instead.

### Avoid

- Jupyter notebooks
- Inventing your own file format.
- Tar files, especially compressed ones.
  These are prone to data loss in case of even the tiniest bit rot.
  Ordinary ZIP is more robust, because every file is compressed individually.
- Compressed files inside compressed files.
- Binary files in general, are harder to reuse in the longer term.
- HDF5 files due to their data integrity issues.
- Python pickle files,
  as these can only be loaded when the corresponding Python packages are around.
  This is too limiting for long-term data preservation.
- Files that can only be used with closed-source software.


## Software

### Must

- List software dependencies in `requirements.txt` or `environment.yaml`,
  such that they can be installed with `pip` or `conda` by all co-authors.
  Specify the version (if relevant).

- All software to rebuild the publication must be open source.

- When you have the choice, do not use closed-source software.

- If you generate some data with closed-source software, store it in a `dataset-<name>`
  directory and document in the `README.md` how you exactly generated the data
  and with which versions of the software.

- If you write your own Python package and use it in a publication,
  make open-source releases of all versions used in the paper.
  In addition to `requirements.txt` or `environment.yaml`,
  also refer to the source repository and the version of your package in the `README.md`
  of the corresponding `results-<name>` or `dataset-<name>` directories.

    If your Python package is highly experimental and you're not comfortable releasing it yet,
    you can include it in the publication project repository,
    for example, under `latest-draft/pkgs/your_package`.
    You can then add a line `-e latest-draft/pkgs/your_package`
    to the `requirements.txt` and `environment.yaml` files as follows:

    **requirements.txt** (just add a line)
    ```
    -e latest-draft/pkgs/your_package
    ```

    **environment.yaml** (add a line under the `pip` item)
    ```
    - pip:
    - '-e latest-draft/pkgs/your_package'
    ```
