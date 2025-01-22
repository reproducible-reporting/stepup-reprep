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
        Panel(0, 2, "(e) vertical", "vertical.pdf", nrow=2),
        Panel(2, 0, "(f) horizontal", "horizontal.pdf", ncol=3),
    ],
    fontname="bitsvera",
    # TTF obtained from https://download.gnome.org/sources/ttf-bitstream-vera/1.10/
    fontfile="vera.ttf",
)


if __name__ == "__main__":
    driver(FIGURE)
