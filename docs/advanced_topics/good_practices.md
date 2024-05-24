# Good Practices

This tutorial lists some recommendations that facilitate data accuracy, reuse and reproducibility
when working on a StepUp RepRep project.

The [first section](#summaries) offers a compact summary of recommendations,
which refer to parts of the [second section](#motivations) for more background
and motivations behind the recommendations.

## Summaries

The summaries below are grouped into categories and within each categeory several classes of recommendations exist:

- *"Must"* recommendations are highly encouraged.
  Even when you have started of neglecting some of these recommendations,
  you would benefit from converting your repository to adhere to these points.
- *"Should"* recommendation are also encouraged but are considered less pressing.
  There can be external factors (e.g. publisher) that force you to digress.


### Filename Conventions

#### Must

- Use semantic file and directory names to organize your data.
- When directory or file names contain numbers, zero-pad them
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

- Similarly, keywords can be padded with dashes or underscores, for example:

    ```
    opt__low
    opt_high
    ```

- When using a similar structure inside multiple directories, use
  exactly the same filenames within the directories.
  This facilitates automation.

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


### Tex Sources

#### Must

- All documents are written in LaTeX.
- Every unused LaTeX package is a good package.
- Each sentence starts on a new line in the LaTeX source.
- To facilitate reviewing the PDF, use single-column and double-line spacing.
- Use [BibSane](https://github.com/reproducible-reporting/bibsane) to keep your BibTeX files sane.
  Hint: [Quick DOI to BIB conversion](https://www.doi2bib.org)
- Avoid `\subfigure`. Merge panels into one PDF instead. (See [Tile PDFs](tile_pdfs.md).)


#### Should

- Some packages, like `todo`, are convenient while writing.
  Clearly separate these from other `\usepackage` lines, so they can be easily deleted
  when finalizing the manuscript.
- Define as few commands as possible.
- Avoid low-quality publisher article classes. (ACS has a decent one.)


### Figures

#### Must

- Separate data generation or collection from actual plotting:
  Perform these two steps in separate Python scripts.
  This means committing the following to Git:

    - Data files (e.g., CSV) containing plot data, including generated data.
      This allows for verification of reproducibility.

    - Scripts generating data, if applicable.

    - Scripts generating plots using the above data as input.
      Use matplotlib unless otherwise justified.

    - A `README.md` or docstrings summarizing scripts and data.

- When creating drawings, use Inkscape (>= 1.2) and commit SVG source files.

- Use bitmap formats only as an intermediate format
  when vector graphics PDFs show performance issues.
  This typically happens with plots containing many thousands of data points:
  Use high-resolution PNG files (not GIF, JPEG or other formats).

- [Avoid Jupyter notebooks](#jupyter-notebooks) as a tool to make figures with Python scripts.


### Tables

#### Must

Commit the following:

- Machine-readable files (e.g., CSV) containing table data.
- Scripts generating LaTeX source for tables.
- A `README.md` or docstrings summarizing scripts and data.
- [Avoid Jupyter notebooks](#jupyter-notebooks) as a tool to make tables with Python scripts.


### Data Sets

#### Must

- Use `dataset-{name}` directories for data that cannot be (easily) generated from scratch.
  For example.

    - External data sets.
    - Expensive calculations done previously.
    - (Large amounts of) experimental measurements.
    - Data generated with closed-source software.
      (Avoid closed-source software when you have the choice.)
    - Data created with specialized hardware not generally available.
    - Manually curated data.

- Add scripts and implementations to regenerate the data,
  integrating them as much as possible with StepUp RepRep.

- Add a `README.md` file explaining:

    - How the data were generated.
    - Software that was used.
    - Directory and file organization.
    - File content details.

- Data sets will be Zipped in the end, so store uncompressed data in the repository.

- [Avoid Jupyter notebooks](#jupyter-notebooks) as a tool to work on datasets.

- Do not invent your own file formats.

- Do not use tar files, especially compressed ones, due to data loss concerns.
  Ordinary ZIP is more robust, because every file is compressed individually.

- [Do not use HDF5 files](#hdf5) due to their data integrity issues.

- Do not use Python pickle files,
  as these can only be loaded when the corresponding Python packages are around.
  This is too limiting for long-term data preservation.

- Do not use file formats that can only be used with closed-source software.


#### Should

- When data sets exceed 500 kB, use [Git LFS](https://git-lfs.com/).
  The threshold can be increased for convenience,
  but consider remote Git repository storage quota.
  For GitHub, the maximum seems to be 5 GB at the moment (for the entire history).

- When data sets become large for Git LFS (more than 50 MB), use University-provided storage.
  Check your Git LFS quota to define a sensible threshold.
  At the time of writing, this is 2 GB (all files combined) for GitHub.
  When offloading data outside the Git repository,
  document clearly where the data is stored, how to access and who has access permissions.

- For some files, such as zipped collections of data files,
  there are no concerns that the zipping itself is difficult to reproduce,
  so you can decide not to store the zip file separately and add it to `.gitignore` instead.

- Do not store compressed files inside compressed files.
  This is usually inefficient and increase the risk of large data losses due to bitrot.

- Avoid binary files in general, are harder to reuse in the longer term.


### Software

#### Must

- List software dependencies in `requirements.txt` or `environment.yaml`,
  specifying versions where relevant,
  to enable installation with `pip` or `conda` by all co-authors.

- Use only open-source software to (re)build the publication.

- When possible, avoid using closed-source entirely.

- If you generate some data with closed-source software, store it in a `dataset-<name>`
  directory and document in the `README.md` how you exactly generated the data
  and which versions of the software were used.

- If you write your own Python package and use it in a publication,
  make open-source releases of all versions used in the paper.
  In addition to `requirements.txt` or `environment.yaml`,
  refer to the source repository and the version of your package in the `README.md`
  of the corresponding `results-<name>` or `dataset-<name>` directories.

    If your Python package is experimental and not ready for release yet,
    include it in the publication project repository under `latest-draft/pkgs/your_package`.
    Add a line `-e latest-draft/pkgs/your_package`
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


## Details

This section contains some more background on the recommendations given above.
Keep in mind that this section is work in progress.

### Jupyter Notebooks

Jupyter Notebooks are very popular for interactive Python programming because
you can combine documentation, code and visualization in one document.
Despite their popularity, they also have inherent limitations that are not easy to overcome:

- Changes to Jupyter notebooks are not easily visualized with textual diffs.
- Related to the previous point:
  Collaborating on Jupyter notebooks via version control is problematic.
  Merging different contributions to notebooks easily leads to invalid PYNB files.
- You can execute code cells in notebooks in any order, which can lead to incorrect results.
- You cannot easily import Jupyter notebooks into other notebooks,
  making them non-modular and monolithic.
  The only way to reuse code from one notebook in another is to copy and paste fragments.

For these reasons, we recommend avoiding them and instead working with reproducible workflows that
combine scripts and analysis tools in Python modules (or packages) and Markdown files.


### HDF5

If a process is killed while writing to an HDF5 file,
there is a tiny chance that the entire file will become unreadable,
not just the part that was being written.
Such an abrupt process termination can never be ruled out (e.g., power failure).
We are not aware of any recent fixes for this, e.g.,
some form of journaling may make the format resilient to interrupted writes.
This happens so rarely that the issue is often dismissed as irrelevant,
see https://news.ycombinator.com/item?id=10860496

[Zarr](https://zarr.readthedocs.io/en/stable/) is an alternative to HDF5
that has comparable features but does not have the catastrophic data loss issue
because it writes different arrays to different files.
It relies on the robustness of journaling at the file system level,
and so does not need to reimplement it at the file format level.
Zarr does not support some of the extreme performance features of HDF5,
just to say that nothing is perfect.
Still, reliability beats performance, because losing data is a waste of time.

For less demanding applications,
[Numpy's](https://numpy.org/doc/stable/reference/generated/numpy.savez.html) NPY and NPZ
may be a good fit.
Their main advantage is the simplicity and availability within NumPy.

Some online discussions on the topic:

- [https://forum.hdfgroup.org/t/avoiding-corruption-of-the-hdf5-file/4087](https://forum.hdfgroup.org/t/avoiding-corruption-of-the-hdf5-file/4087) (2018)
- [https://forum.hdfgroup.org/t/corrupted-file-due-to-shutdown/9658](https://forum.hdfgroup.org/t/corrupted-file-due-to-shutdown/9658) (2022)
- [https://janert.me/blog/2022/looking-at-hdf5/](https://janert.me/blog/2022/looking-at-hdf5/) (2022)
