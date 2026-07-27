#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import compile_typst

static("template.typ", "persons.json")
compile_typst("template.typ", "persons.pdf", inp="persons.json", sysinp={"json": "persons.json"})
