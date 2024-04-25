#!/usr/bin/env python

from stepup.core.api import static, step
from stepup.reprep.api import latex

static("paper.tex")
static("smile.pdf")
latex("paper.tex")
step("echo 'Hi there!' > generated.tex", out=["generated.tex"])
