#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import render

static("template.md", "variables.py")
render("template.md", ["variables.py"], "rendered.md")
