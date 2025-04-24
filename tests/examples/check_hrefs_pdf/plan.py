#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import check_hrefs, compile_latex

static("README.txt", "main.tex", "check_hrefs.yaml")
compile_latex("main.tex", inventory=True)
check_hrefs("main.pdf")
