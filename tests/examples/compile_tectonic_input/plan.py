#!/usr/bin/env python3

from stepup.core.api import run, static
from stepup.reprep.api import compile_tectonic

static("paper.tex")
static("smile.pdf")
compile_tectonic("paper.tex", keep_deps=True)
run("echo 'Hi there!' > generated.tex", out=["generated.tex"], shell=True)
