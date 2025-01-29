#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import compile_latex

static("paper.tex")
static("bibsane.yaml")
static("references.bib")
compile_latex("${LATEX_MAIN}.tex")
