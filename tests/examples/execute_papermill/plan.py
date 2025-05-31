#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import execute_papermill

static("demo.ipynb", "data.json", "points.txt")
execute_papermill(
    "demo.ipynb", "demo_out.ipynb", inp="points.txt", out="plot.png", parameters={"dpi": 50}
)
