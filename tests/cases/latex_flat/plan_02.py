#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import latex_flat

static("sub/")
static("sub/other.tex")
static("article_structured.tex", "part1.tex", "part2.tex")
latex_flat("article_structured.tex", "article.tex")
