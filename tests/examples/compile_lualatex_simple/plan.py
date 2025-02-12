#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import compile_latex

static("paper.tex")
compile_latex("paper.tex", inventory=True)
