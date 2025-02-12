#!/usr/bin/env python3
from stepup.core.api import glob, static
from stepup.reprep.api import render_jinja

static("template.txt")
for path_variables in glob("trip*.yaml"):
    render_jinja("template.txt", path_variables, f"rendered-{path_variables.stem}.txt")
