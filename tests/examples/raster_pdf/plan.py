#!/usr/bin/env python3
from stepup.core.api import mkdir, static
from stepup.reprep.api import raster_pdf

static("smile.pdf")
mkdir("rastered")
raster_pdf("smile.pdf", "rastered/")
