#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import compile_typst

static("*.typ", "*.svg", "*.png")
compile_typst("demo.typ", keep_deps=True)
