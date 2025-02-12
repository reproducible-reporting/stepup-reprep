#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import render_jinja

static("template.txt")
trips = [{"place": "Barcelona", "animal": "a pigeon"}, {"place": "Reykjavik", "animal": "a puffin"}]
for i, trip in enumerate(trips):
    render_jinja("template.txt", trip, f"rendered-trip{i+1}.txt")
