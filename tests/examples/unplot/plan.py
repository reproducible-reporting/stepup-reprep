#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import unplot

static("plot1.svg", "plot2.svg")
unplot("plot1.svg", "current_plot1.json")
unplot("plot2.svg", "current_plot2.json")
