#!/usr/bin/env python3
from stepup.core.api import glob, script, static
from stepup.reprep.api import convert_pdf_png, convert_svg_pdf

for path_svg in glob("*.svg"):
    convert_svg_pdf(path_svg)
static("tile.py")
script("tile.py")
convert_pdf_png("figure.pdf", resolution=150)
