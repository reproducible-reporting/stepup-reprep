#!/usr/bin/env python

from stepup.core.api import static
from stepup.reprep.api import check_hrefs, latex

static("README.md", "main.tex", "check_hrefs.yaml")
latex("main.tex")
check_hrefs("main.pdf")
