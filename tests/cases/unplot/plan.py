#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import unplot

static("plot.svg")
unplot("plot.svg", "current_plot.json")
