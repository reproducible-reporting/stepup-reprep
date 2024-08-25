# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# Copyright (C) 2024 Toon Verstraelen
#
# This file is part of StepUp RepRep.
#
# StepUp RepRep is free software;  you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# StepUp RepRep is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
"""Extract data points from plots."""

import argparse
import json
from xml.dom.minidom import Element, parse

import attrs
import numpy as np
from numpy.typing import NDArray
from path import Path
from svg.path import parse_path


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    x_axis, y_axis, px_curves = load_pixel_data_svg(args.inp)
    curves = {
        label: transform_pixel_data(x_axis, y_axis, px_curve).tolist()
        for label, px_curve in px_curves.items()
    }
    with open(args.out, "w") as fh:
        json.dump(curves, fh, indent=2)
        fh.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-unplot", description="Extract data points from bitmap plots."
    )
    parser.add_argument("inp", type=Path, help="SVG file with paths drawn on top of the image")
    parser.add_argument("out", type=Path, help="Output JSON file with extracted data points")
    return parser.parse_args(argv)


@attrs.define
class Axis:
    """Extracted data of an x- or y-axis."""

    start: NDArray = attrs.field()
    end: NDArray = attrs.field()
    low: float = attrs.field(converter=float)
    high: float = attrs.field(converter=float)
    kind: str = attrs.field(validator=attrs.validators.in_(["lin", "log"]))


def load_pixel_data_svg(filename: str) -> tuple[Axis, Axis, dict[str, NDArray]]:
    """Load elements from an SVG file, keeping all data in the units of the SVG drawing.

    Parameters
    ----------
    filename
        The SVG file to load.

    Returns
    -------
    x_axis
        The x-axis in the drawing.
    y_axis
        The y-axis in the drawing.
    pixel_curves
        A dictionary with curve data loaded from the plot.
        The keys are labels extracted from the path id.
        The values are NumPy arrays of which the rows are (x, y) data points.
    """
    x_axis = None
    y_axis = None
    px_curves = {}
    dom = parse(filename)
    paths = dom.getElementsByTagName("path")
    for path in paths:
        name = path.getAttribute("id")
        if name.startswith("xaxis"):
            if x_axis is not None:
                raise ValueError("X-axis defined twice.")
            x_axis = parse_axis(name, path)
        elif name.startswith("yaxis"):
            if y_axis is not None:
                raise ValueError("X-axis defined twice.")
            y_axis = parse_axis(name, path)
        elif name.startswith("data:"):
            px_curves[name[5:]] = parse_curve(path)

    if x_axis is None:
        raise ValueError("No x-axis found.")
    if y_axis is None:
        raise ValueError("No y-axis found.")
    if len(px_curves) == 0:
        raise ValueError("No curve with data points found.")
    return x_axis, y_axis, px_curves


def parse_axis(name: str, path: Element) -> Axis:
    """Convert an SVG Path to an x- or y-axis."""
    result = extract_svg_path(path.getAttribute("d"))
    if len(result) != 2:
        raise ValueError(f"Expected two points, got {len(result)} ({name})")
    words = name.split(":")
    return Axis(result[0], result[1], words[1], words[2], words[3])


def parse_curve(path: Element) -> NDArray:
    """Convert an SVG Path to an array of data points."""
    return extract_svg_path(path.getAttribute("d"))


def extract_svg_path(d: str) -> NDArray:
    """Convert SVG path commands into an array of data points."""
    path = parse_path(d)
    result = []
    for item in path:
        for point in item.start, item.end:
            if len(result) == 0 or result[-1] != point:
                result.append(point)
    return np.array([[point.real, point.imag] for point in result])


def transform_pixel_data(x_axis: Axis, y_axis: Axis, px_curve: NDArray) -> NDArray:
    """Convert data in drawing coordinates to axes coordinates."""
    # construct x- and y-unit vectors in pixel coordinates
    px_xunit = x_axis.end - x_axis.start
    px_yunit = y_axis.end - y_axis.start

    # the affine transformation to pixel coordinates
    mat_to_pix = np.array([px_xunit, px_yunit]).T

    # the inverse affine transformation
    mat_from_pix = np.linalg.inv(mat_to_pix)

    # reference point for the x and y values
    x_low = np.dot(mat_from_pix, x_axis.start)
    y_low = np.dot(mat_from_pix, y_axis.start)

    # transform the datapoints to data coordinates
    data = np.dot(mat_from_pix, px_curve.T)
    data[0] -= x_low[0]
    data[1] -= y_low[1]

    # convert to plot units
    convert_unit(data[0], x_axis)
    convert_unit(data[1], y_axis)

    return data


def convert_unit(values: NDArray, axis: Axis):
    """Transform data in place to axis coordinates.

    The values are assumed to be transformed to dimensionless coordintes first.
    """
    if axis.kind == "lin":
        values[:] = values * (axis.high - axis.low) + axis.low
    elif axis.kind == "log":
        llow = np.log(axis.low)
        lhigh = np.log(axis.high)
        values[:] = np.exp(values * (lhigh - llow) + llow)
    else:
        raise ValueError(f"Unsupported axis kind: {axis.kind}")


if __name__ == "__main__":
    main()
