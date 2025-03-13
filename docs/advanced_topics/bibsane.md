# Sanitizing BibTeX files

!!! note

    Bibsane is integrated into StepUp RepRep as of version 2.3.

StepUp RepRep can clean up BibTeX files to fix issues
that would otherwise be difficult to spot or require tedious manual edits.
This feature was formerly implemented in an external tool called `bibsane`,
but is now integrated into StepUp RepRep.
The cleanup must always be performed after building the LaTeX document,
to be able to identify unused records.

The following is a minimal example of the commands in a `plan.py` file that will clean up a BibTeX file:

```python
from stepup.core.api import static
from stepup.reprep.api import compile_latex, sanitize_bibtex

static("paper.tex", "references.bib")
compile_latex("paper.tex")
sanitize_bibtex("paper.aux")
```

The [`sanitize_bibtex()`][stepup.reprep.api.sanitize_bibtex] function will read the `.aux` file(s)
to identify the `.bib` files used.
By default, it assumes there is just one `.bib` file and rewrites it with the cleaned-up content.
If there are multiple `.bib` files, you can specify an output file with `path_out="clean.bib"`.

The `sanitize_bibtex()` function also accepts a `path_cfg` argument to specify
a YAML configuration file for `rr-bibsane`, i.e. the script that actually implements the cleanup.
(Without configuration file, a minimal cleanup is performed.)
For example, you can create a `bibsane.yml` file with the following content
to enable more checks and cleanups:

```yaml
drop_entry_types: ["control"]
normalize_doi: true
duplicate_id: merge  # other options: fail or ignore
duplicate_doi: merge  # other options: fail or ignore
preambles_allowed: false
normalize_whitespace: true
fix_page_double_hyphen: true
# PyISO4 can be used to abbreviate journal names.
abbreviate_journal: true
custom_abbreviations:
    CRAZY J0rnAL: Crazy J.
sort: true  # sort key = {year}{first author lowercase normalized name}
citation_policies:
  article:
    author: must
    journal: must
    number: may
    pages: must
    title: must
    volume: must
    year: must
    doi: must
  book:
    author: must
    title: must
    publisher: must
    year: must
    month: must
    isbn: must
  misc.url:
    title: must
    url: must
    urldate: must
  misc.dataset:
    author: must
    title: must
    year: must
    doi: must
    urldate: must
    publisher: must
```

Everything above `citation_policies` consists of global settings.
See [`BibsaneConfig`][stepup.reprep.bibsane.BibsaneConfig] for a full list of available settings.

Under `citation_policies` you can specify which keys are expected and allowed for each entry type.
The `misc` entry type is a catchall for diverse citations,
so you can specify subtypes like `misc.url` and `misc.dataset`.
In your BibTeX file, you can identify the subtype by adding a `bibsane` field.
For example:

```bibtex
@misc{doe2025,
 author = {John Doe},
 bibsane = {misc.dataset},
 doi = {10.5281/zenodo.0123456},
 publisher = {Zenodo},
 title = {Some data set, Version 1},
 urldate = {2025-02-12},
 year = {2025}
}
```
