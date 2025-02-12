#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import compile_typst

static("belgium.typ")
compile_typst("belgium.typ", "flag.png", resolution=30)
