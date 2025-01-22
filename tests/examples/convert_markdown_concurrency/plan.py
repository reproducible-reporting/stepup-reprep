#!/usr/bin/env python3
from stepup.core.api import static, step
from stepup.reprep.api import convert_markdown

static("macros.tex")
for i in range(20):
    fn_random = f"random_{i:02d}.md"
    step(f"./write.py {i} > {fn_random}", out=fn_random)
    convert_markdown(fn_random, katex=True, path_macro="macros.tex")
