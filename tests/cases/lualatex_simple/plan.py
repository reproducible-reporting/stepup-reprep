#!/usr/bin/env python

from stepup.core.api import static
from stepup.reprep.api import latex

static("paper.tex")
latex("paper.tex")
