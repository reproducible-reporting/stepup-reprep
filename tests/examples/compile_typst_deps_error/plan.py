#!/usr/bin/env python3
from stepup.core.api import run, static
from stepup.reprep.api import compile_typst

static("document.typ")
compile_typst("document.typ")
run("echo 'fixed: new' > data.yaml", out="data.yaml", shell=True)
