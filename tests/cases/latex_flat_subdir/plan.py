#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import latex_flat

static("sub/", "sub/article_structured.tex", "sub/part1.tex", "sub/part2.tex")
latex_flat("sub/article_structured.tex", "sub/article.tex")
