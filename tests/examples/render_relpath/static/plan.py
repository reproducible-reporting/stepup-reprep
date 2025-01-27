#!/usr/bin/env python3
from stepup.reprep.api import getenv, latex, render_jinja

PUBLIC = getenv("PUBLIC", back=True)
render_jinja("main.tex", ["../variables.py", "variables.py"], PUBLIC)
latex("main.tex", workdir=PUBLIC)
