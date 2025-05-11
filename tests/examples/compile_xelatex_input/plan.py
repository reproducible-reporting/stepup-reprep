#!/usr/bin/env python3

from stepup.core.api import mkdir, runsh, static
from stepup.reprep.api import compile_latex

static("paper.tex")
mkdir("subdir/")
compile_latex("paper.tex", inventory=True)
runsh(
    "echo 'Verbatim input:\\verbatiminput{code.txt}' > subdir/generated.tex",
    out=["subdir/generated.tex"],
)
runsh("echo '2 + 2' > subdir/code.txt", out=["subdir/code.txt"])
