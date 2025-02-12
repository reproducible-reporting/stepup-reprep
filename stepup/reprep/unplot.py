# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# © 2024–2025 Toon Verstraelen
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
from xml.etree.ElementTree import Element

import attrs
import numpy as np
from defusedxml.ElementTree import iterparse
from numpy.typing import NDArray
from path import Path
from svg.path import parse_path


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    axes, px_curves = load_pixel_data_svg(args.inp)
    data = {
        "units": {axis.label: axis.units for axis in axes},
        "curves": {
            label: transform_pixel_data(axes, px_curve) for label, px_curve in px_curves.items()
        },
    }
    with open(args.out, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-unplot", description="Extract data points from bitmap plots."
    )
    parser.add_argument("inp", type=Path, help="SVG file with paths drawn on top of the image")
    parser.add_argument("out", type=Path, help="Output JSON file with extracted data points")
    return parser.parse_args(argv)


@attrs.define
class Axis:
    """Extracted data of an x- or y-axis."""

    start: NDArray = attrs.field()
    end: NDArray = attrs.field()
    label: str = attrs.field()
    low: float = attrs.field(converter=float)
    high: float = attrs.field(converter=float)
    scale: str = attrs.field(validator=attrs.validators.in_(["linear", "log"]))
    units: str = attrs.field()


def load_pixel_data_svg(filename: str) -> tuple[list[Axis], dict[str, NDArray]]:
    """Load elements from an SVG file, keeping all data in the units of the SVG drawing.

    Parameters
    ----------
    filename
        The SVG file to load.

    Returns
    -------
    axes
        The two axes of the plot.
    pixel_curves
        A dictionary with curve data loaded from the plot.
        The keys are labels extracted from the path id.
        The values are NumPy arrays of which the rows are (x, y) data points.
    """
    px_curves = {}
    axes = []
    parser = iterparse(filename, events=("start",))
    for event, elem in parser:
        if event == "start":
            tag = elem.tag.rpartition("}")[2]
            if tag == "path":
                if "axis" in elem.attrib:
                    axes.append(parse_axis(elem))
                elif "data" in elem.attrib:
                    label = elem.attrib["data"]
                    px_curve = parse_curve(elem)
                    px_curves[label] = px_curve
        elem.clear()

    if len(axes) != 2:
        raise ValueError(f"Expecting two axes, got {len(axes)}")
    if len(px_curves) == 0:
        raise ValueError("No curve with data points found.")
    return axes, px_curves


def parse_axis(path: Element) -> Axis:
    """Convert an SVG Path to an x- or y-axis."""
    id_ = path.attrib["id"]
    nodes = extract_svg_path(path.attrib["d"])
    if len(nodes) != 2:
        raise ValueError(f"Expected two nodes, got {len(nodes)} ({id_})")
    label = path.attrib.get("axis")
    if label is None:
        raise ValueError(f"An axis has no required axis attribute ({id_})")
    low = path.attrib["low"]
    high = path.attrib["high"]
    scale = path.attrib["scale"]
    units = path.attrib["units"]
    return Axis(nodes[0], nodes[1], label, low, high, scale, units)


def parse_curve(path: Element) -> NDArray:
    """Convert an SVG Path to an array of data points."""
    return extract_svg_path(path.attrib["d"])


def extract_svg_path(d: str) -> NDArray:
    """Convert SVG path commands into an array of data points."""
    path = parse_path(d)
    result = []
    for item in path:
        for point in item.start, item.end:
            if len(result) == 0 or result[-1] != point:
                result.append(point)
    return np.array([[point.real, point.imag] for point in result])


def transform_pixel_data(axes: list[Axis], px_curve: NDArray) -> NDArray:
    """Convert data in drawing coordinates to axes coordinates."""
    if len(axes) != 2:
        raise ValueError(f"Expecting two axes, got {len(axes)}")
    # The labels x and y are a bit arbitrary,
    # because any affine transformation of the axes is supported.
    x_axis, y_axis = axes

    # Construct x- and y-unit vectors in pixel coordinates.
    px_xunit = x_axis.end - x_axis.start
    px_yunit = y_axis.end - y_axis.start

    # The affine transformation to pixel coordinates.
    mat_to_pix = np.array([px_xunit, px_yunit]).T

    # The inverse affine transformation.
    mat_from_pix = np.linalg.inv(mat_to_pix)

    # Reference point for the x and y values.
    x_low = np.dot(mat_from_pix, x_axis.start)
    y_low = np.dot(mat_from_pix, y_axis.start)

    # Transform the datapoints to data coordinates.
    data = np.dot(mat_from_pix, px_curve.T)
    data[0] -= x_low[0]
    data[1] -= y_low[1]

    # Convert to plot units.
    convert_unit(data[0], x_axis)
    convert_unit(data[1], y_axis)

    # Associate the data with the axis labels, instead of x and y.
    return {x_axis.label: data[0].tolist(), y_axis.label: data[1].tolist()}


def convert_unit(values: NDArray, axis: Axis):
    """Transform data in place to axis coordinates.

    The values are assumed to be transformed to dimensionless coordintes first.
    """
    if axis.scale == "linear":
        values[:] = values * (axis.high - axis.low) + axis.low
    elif axis.scale == "log":
        llow = np.log(axis.low)
        lhigh = np.log(axis.high)
        values[:] = np.exp(values * (lhigh - llow) + llow)
    else:
        raise ValueError(f"Unsupported axis scale: {axis.scale}")


if __name__ == "__main__":
    main()
