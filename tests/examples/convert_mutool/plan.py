#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_mutool_png

static("example.pdf")
convert_mutool_png("example.pdf", resolution=100)
