#!/usr/bin/env python3
from stepup.core.api import runsh, static
from stepup.reprep.api import compile_typst

static("image.py", "document.typ")
compile_typst("document.typ")
runsh("./image.py", out="image.jpg")
