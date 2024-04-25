#!/usr/bin/env python
from stepup.core.api import glob, script, static
from stepup.reprep.api import convert_svg_pdf

for path_svg in glob("*.svg"):
    convert_svg_pdf(path_svg)
static("tile.py", "vera.ttf")
script("tile.py")
