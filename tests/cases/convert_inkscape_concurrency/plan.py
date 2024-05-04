#!/usr/bin/env python
from stepup.core.api import glob
from stepup.reprep.api import convert_svg_pdf

for path_svg in glob("*.svg"):
    convert_svg_pdf(path_svg)
