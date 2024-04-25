#!/usr/bin/env python
from stepup.reprep.api import getenv, latex, render

PUBLIC = getenv("PUBLIC", is_path=True)
render("main.tex", ["../variables.py", "variables.py"], PUBLIC)
latex("main.tex", workdir=PUBLIC)
