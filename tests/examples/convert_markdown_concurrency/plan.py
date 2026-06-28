#!/usr/bin/env python3
from stepup.core.api import run
from stepup.reprep.api import convert_markdown

for i in range(20):
    fn_random = f"random_{i:02d}.md"
    run(f"./write.py {i} > {fn_random}", out=fn_random, shell=True)
    convert_markdown(fn_random)
