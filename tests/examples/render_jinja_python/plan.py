#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import render_jinja

static("template.md", "variables.py")
render_jinja("template.md", "variables.py", "rendered.md")
