#!/usr/bin/env python3
from stepup.reprep.api import getenv, latex, render

PUBLIC = getenv("PUBLIC", back=True)
render("main.tex", ["../variables.py", "variables.py"], PUBLIC)
latex("main.tex", workdir=PUBLIC)
