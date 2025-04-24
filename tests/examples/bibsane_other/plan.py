#!/usr/bin/env python3
from stepup.core.api import copy, static
from stepup.reprep.api import sanitize_bibtex

static("references.bib", "paper.aux", "bibsane.yaml")
sanitize_bibtex(
    "references.bib", path_aux="paper.aux", path_cfg="bibsane.yaml", path_out="cleaned.bib"
)
copy("cleaned.bib", "copy.bib")
