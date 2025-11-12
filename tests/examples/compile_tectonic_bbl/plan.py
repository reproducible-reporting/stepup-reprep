#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import compile_tectonic

static("paper.tex")
static("paper.bbl")
compile_tectonic("paper.tex", inventory=True)
