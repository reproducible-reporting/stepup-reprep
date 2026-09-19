#!/usr/bin/env python3

from stepup.core.api import run, static
from stepup.reprep.api import compile_latex

static("sub/paper.tex", "sub/smile.pdf", "sub/references.bib")
compile_latex("sub/paper.tex", inventory=True)
run("echo 'Hi there!' > generated.tex", out=["generated.tex"], workdir="sub", shell=True)
