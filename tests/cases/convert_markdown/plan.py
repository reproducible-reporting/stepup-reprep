#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import convert_markdown

static("demo.md", "macros.tex")
convert_markdown("demo.md", katex=True, path_macro="macros.tex")
