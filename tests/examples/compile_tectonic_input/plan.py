#!/usr/bin/env python3

from stepup.core.api import runsh, static
from stepup.reprep.api import compile_tectonic

static("paper.tex")
static("smile.pdf")
compile_tectonic("paper.tex", keep_deps=True)
runsh("echo 'Hi there!' > generated.tex", out=["generated.tex"])
