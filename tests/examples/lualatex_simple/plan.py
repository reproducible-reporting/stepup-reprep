#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import latex

static("paper.tex")
latex("paper.tex")
