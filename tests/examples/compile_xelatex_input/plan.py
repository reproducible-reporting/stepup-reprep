#!/usr/bin/env python3

from stepup.core.api import mkdir, static, step
from stepup.reprep.api import compile_latex

static("paper.tex")
mkdir("subdir/")
compile_latex("paper.tex", inventory=True)
step(
    "echo 'Verbatim input:\\verbatiminput{code.txt}' > subdir/generated.tex",
    out=["subdir/generated.tex"],
)
step("echo '2 + 2' > subdir/code.txt", out=["subdir/code.txt"])
