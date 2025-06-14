#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import flatten_latex

static("sub/")
static("sub/other.tex")
static("article_structured.tex", "part1.tex", "part2.tex", "part3.txt")
flatten_latex("article_structured.tex", "article.tex")
