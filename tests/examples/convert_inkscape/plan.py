#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_svg_pdf, convert_svg_png

static("smile.svg", "glasses.svg")
convert_svg_png("glasses.svg", optional=True)
convert_svg_pdf("smile.svg", "final.pdf")
