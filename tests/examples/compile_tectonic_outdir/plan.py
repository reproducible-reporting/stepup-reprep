#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import compile_tectonic

static("sub/paper.tex")
compile_tectonic("sub/paper.tex", "out/", inventory=True)
