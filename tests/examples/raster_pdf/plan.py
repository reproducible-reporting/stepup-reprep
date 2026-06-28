#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import raster_pdf

static("smile.pdf")
raster_pdf("smile.pdf", "rastered/")
