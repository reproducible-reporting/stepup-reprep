#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import compile_typst

static("document.typ")
compile_typst("document.typ", "out.pdf", inventory=True)
