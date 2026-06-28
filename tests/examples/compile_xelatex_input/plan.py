#!/usr/bin/env python3

from stepup.core.api import run, static
from stepup.reprep.api import compile_latex

static("paper.tex")
compile_latex("paper.tex", inventory=True)
run(
    "echo 'Verbatim input:\\verbatiminput{code.txt}' > subdir/generated.tex",
    out=["subdir/generated.tex"],
    shell=True,
)
run("echo '2 + 2' > subdir/code.txt", out=["subdir/code.txt"], shell=True)
