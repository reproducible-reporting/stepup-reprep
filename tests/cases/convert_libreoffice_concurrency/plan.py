#!/usr/bin/env python
from stepup.core.api import copy, static
from stepup.reprep.api import convert_odf_pdf

static("something.odt")
for i in range(20):
    copy("something.odt", f"copy_{i:02d}.odt")
    convert_odf_pdf(f"copy_{i:02d}.odt")
