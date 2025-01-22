#!/usr/bin/env python3
from stepup.core.script import driver
from stepup.reprep.tile_pdf import Figure, Panel

FIGURE = Figure(
    "figure.pdf",
    [
        Panel(0, 0, "(a) triangle", "triangle.pdf"),
        Panel(0, 1, "(b) square", "square.pdf"),
        Panel(1, 0, "(c) pentagon", "pentagon.pdf"),
        Panel(1, 1, "(d) hexagon", "hexagon.pdf"),
    ],
)

if __name__ == "__main__":
    driver(FIGURE)
