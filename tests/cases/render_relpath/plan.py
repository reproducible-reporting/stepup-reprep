#!/usr/bin/env python
from stepup.core.api import copy, getenv, glob, mkdir, plan, static

PUBLIC = getenv("PUBLIC", is_path=True)
glob("static/**", _defer=True)
static("variables.py")
mkdir(PUBLIC)
copy("static/preamble.inc.tex", PUBLIC, optional=True)
plan("static/")
