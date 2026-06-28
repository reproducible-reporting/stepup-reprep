#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_markdown

static("source/demo.md")
static("common/")
convert_markdown("source/demo.md")
