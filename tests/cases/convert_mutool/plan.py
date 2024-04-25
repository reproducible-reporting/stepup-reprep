#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import convert_pdf_png

static("example.pdf")
convert_pdf_png("example.pdf", resolution=100)
