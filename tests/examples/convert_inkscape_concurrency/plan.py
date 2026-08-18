#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_inkscape_pdf

for path_svg in static("*.svg"):
    convert_inkscape_pdf(path_svg)
