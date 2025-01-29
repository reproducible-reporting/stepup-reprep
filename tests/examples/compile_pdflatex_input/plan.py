#!/usr/bin/env python3

from stepup.core.api import static, step
from stepup.reprep.api import compile_latex

static("paper.tex")
static("smile.pdf")
compile_latex("paper.tex")
step("echo 'Hi there!' > generated.tex", out=["generated.tex"])
