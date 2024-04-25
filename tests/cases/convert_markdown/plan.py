#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import convert_markdown

static("demo.md")
convert_markdown("demo.md")
