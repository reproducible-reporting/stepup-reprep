#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import convert_odf_pdf

static("slide.odp")
convert_odf_pdf("slide.odp")
