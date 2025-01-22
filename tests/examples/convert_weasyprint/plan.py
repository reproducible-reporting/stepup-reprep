#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_weasyprint

static("doc.html", "block.png", "style.css")
convert_weasyprint("doc.html")
