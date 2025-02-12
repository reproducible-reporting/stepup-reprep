#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import compile_typst

static(
    "source/",
    "source/document.typ",
    "source/tada.svg",
    "source/aux/",
    "source/aux/productivity.csv",
)
compile_typst("source/document.typ", "out.pdf", inventory=True, keep_deps=True)
