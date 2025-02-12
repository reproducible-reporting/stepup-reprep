#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_inkscape_pdf, convert_inkscape_png

static("smile.svg", "glasses.svg")
convert_inkscape_png("glasses.svg", optional=True)
convert_inkscape_pdf("smile.svg", "final.pdf")
