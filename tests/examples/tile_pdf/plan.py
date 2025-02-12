#!/usr/bin/env python3
from stepup.core.api import glob, script, static
from stepup.reprep.api import convert_inkscape_pdf

for path_svg in glob("*.svg"):
    convert_inkscape_pdf(path_svg)
static("tile.py", "vera.ttf")
script("tile.py")
