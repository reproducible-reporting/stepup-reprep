#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import latex

static("paper.tex")
static("bibsane.yaml")
static("references.bib")
latex("${LATEX_MAIN}.tex")
