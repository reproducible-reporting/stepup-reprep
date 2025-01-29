#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import check_hrefs, compile_latex

static("README.md", "main.tex", "check_hrefs.yaml")
compile_latex("main.tex")
check_hrefs("main.pdf")
