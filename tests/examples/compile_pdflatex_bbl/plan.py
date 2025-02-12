#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import compile_latex

static("paper.tex")
static("paper.bbl")
compile_latex("paper.tex", run_bibtex=False, inventory=True)
