#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import compile_typst

static("template.typ")
compile_typst("template.typ", "alice.pdf", sysinp={"name": "Alic", "age": 29})
compile_typst("template.typ", "bob.pdf", sysinp={"name": "Bob", "age": 31})
compile_typst("template.typ", "charlie.pdf", sysinp={"name": "Charlie", "age": 27})
