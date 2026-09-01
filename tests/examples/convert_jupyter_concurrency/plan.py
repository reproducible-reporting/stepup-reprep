#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_jupyter

static("demo.ipynb")
for i in range(8):
    convert_jupyter("demo.ipynb", f"out_{i}.html")
