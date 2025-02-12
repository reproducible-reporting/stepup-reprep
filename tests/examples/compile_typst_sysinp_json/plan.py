#!/usr/bin/env python3
from path import Path

from stepup.core.api import static
from stepup.reprep.api import compile_typst

static("template.typ", "persons.json")
compile_typst("template.typ", "persons.pdf", sysinp={"json": Path("persons.json")})
