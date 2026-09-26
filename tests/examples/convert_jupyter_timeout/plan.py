#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_jupyter

static("slow.ipynb")
convert_jupyter("slow.ipynb", out="result.txt", timeout=1)
