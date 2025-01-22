#!/usr/bin/env python3

from stepup.core.api import static, step
from stepup.reprep.api import latex

static("paper.tex")
static("smile.pdf")
latex("paper.tex")
step("echo 'Hi there!' > generated.tex", out=["generated.tex"])
