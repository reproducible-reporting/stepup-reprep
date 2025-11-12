#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import compile_tectonic, sanitize_bibtex

static("paper.tex")
static("bibsane.yaml")
static("references.bib")
compile_tectonic("${LATEX_MAIN}.tex", inventory=True)
sanitize_bibtex("references.bib", path_cfg="bibsane.yaml")
