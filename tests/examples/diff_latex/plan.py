#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import diff_latex

static("new.tex", "old.tex")
diff_latex("old.tex", "new.tex", "diff.tex")
