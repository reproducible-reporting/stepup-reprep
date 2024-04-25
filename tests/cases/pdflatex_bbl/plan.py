#!/usr/bin/env python

from stepup.core.api import static
from stepup.reprep.api import latex

static("paper.tex")
static("paper.bbl")
latex("paper.tex", run_bibtex=False)
