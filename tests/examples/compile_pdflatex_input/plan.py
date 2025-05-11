#!/usr/bin/env python3

from stepup.core.api import runsh, static
from stepup.reprep.api import compile_latex

static("paper.tex")
static("smile.pdf")
compile_latex("paper.tex")
runsh("echo 'Hi there!' > generated.tex", out=["generated.tex"])
