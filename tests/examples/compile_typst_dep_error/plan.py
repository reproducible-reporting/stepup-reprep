#!/usr/bin/env python3
from stepup.core.api import static, step
from stepup.reprep.api import compile_typst

static("document.typ")
compile_typst("document.typ")
step("echo 'fixed: new' > data.yaml", out="data.yaml")
