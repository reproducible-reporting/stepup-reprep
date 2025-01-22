#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import convert_markdown

static("sub/", "sub/demo.md", "demo.css", "page.css", "macros.tex")
convert_markdown("sub/demo.md", katex=True, path_macro="macros.tex", paths_css="page.css")
