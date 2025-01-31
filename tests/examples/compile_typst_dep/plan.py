#!/usr/bin/env python3
from stepup.core.api import static, step
from stepup.reprep.api import compile_typst

static("image.py", "document.typ")
compile_typst("document.typ")
step("./image.py", out="image.jpg")
