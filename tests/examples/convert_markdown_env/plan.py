#!/usr/bin/env python3
from stepup.core.api import glob, static
from stepup.reprep.api import convert_markdown

static("source/", "source/demo.md")
glob("common/**", _defer=True)
convert_markdown("source/demo.md")
