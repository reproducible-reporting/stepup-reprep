#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import compile_typst

static("error.typ")
compile_typst("error.typ")
