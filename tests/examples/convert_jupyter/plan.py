#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_jupyter

static("demo.ipynb", "data.json", "points.txt")
convert_jupyter("demo.ipynb", inp="points.txt", out="plot.png", nbargs={"dpi": 50})
