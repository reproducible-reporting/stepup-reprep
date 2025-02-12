#!/usr/bin/env python3
from stepup.reprep.api import compile_latex, getenv, render_jinja

PUBLIC = getenv("PUBLIC", back=True)
render_jinja("main.tex", "../variables.py", "variables.py", PUBLIC)
compile_latex("main.tex", workdir=PUBLIC)
