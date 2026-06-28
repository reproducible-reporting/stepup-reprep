#!/usr/bin/env python3

from stepup.core.api import run, static
from stepup.reprep.api import compile_latex

static("paper.tex")
static("smile.pdf")
compile_latex("paper.tex")
run("echo 'Hi there!' > generated.tex", out=["generated.tex"], shell=True)
