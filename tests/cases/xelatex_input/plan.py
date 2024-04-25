#!/usr/bin/env python

from stepup.core.api import mkdir, static, step
from stepup.reprep.api import latex

static("paper.tex")
mkdir("subdir/")
latex("paper.tex")
step(
    "echo 'Verbatim input:\\verbatiminput{code.txt}' > subdir/generated.tex",
    out=["subdir/generated.tex"],
)
step("echo '2 + 2' > subdir/code.txt", out=["subdir/code.txt"])
