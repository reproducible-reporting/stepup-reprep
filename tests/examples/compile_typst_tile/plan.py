#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import compile_typst

static(
    "figure.typ",
    "hexagon.png",
    "horizontal.pdf",
    "pentagon.jpg",
    "square.webp",
    "triangle.gif",
    "vertical.svg",
)
compile_typst("figure.typ")
