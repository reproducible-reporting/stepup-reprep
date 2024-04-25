#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import latex_diff

static("new.tex", "old.tex")
latex_diff("old.tex", "new.tex", "diff.tex")
