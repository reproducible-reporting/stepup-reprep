#!/usr/bin/env python3

from stepup.core.api import run, static
from stepup.reprep.api import compile_tectonic

static("sub/paper.tex", "sub/smile.pdf", "sub/references.bib")
compile_tectonic("sub/paper.tex", keep_deps=True, inventory=True)
run("echo 'Hi there!' > generated.tex", out=["generated.tex"], workdir="sub", shell=True)
