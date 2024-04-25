#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import convert_weasyprint

static("doc.html")
convert_weasyprint("doc.html")
