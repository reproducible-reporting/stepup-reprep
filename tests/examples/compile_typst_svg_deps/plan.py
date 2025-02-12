#!/usr/bin/env python3
from stepup.core.api import glob
from stepup.reprep.api import compile_typst

glob("*.typ")
glob("*.svg")
glob("*.png")
compile_typst("demo.typ", keep_deps=True)
