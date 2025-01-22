#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_odf_pdf

static("slide.odp")
convert_odf_pdf("slide.odp")
