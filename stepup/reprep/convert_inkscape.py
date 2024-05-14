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
"""Wrapper for SVG to PDF convrsion."""

import argparse
import re
import sys

from path import Path

from stepup.core.api import getenv, step


def main() -> int:
    """Main program."""
    args = parse_args()
    path_out = Path(args.path_out)
    allowed_extensions = [".pdf", ".png"]
    if not any(path_out.endswith(ext) for ext in allowed_extensions):
        print(
            f"The output must have one of the following extensions: {allowed_extensions}",
            file=sys.stderr,
        )
        return -1
    if args.inkscape is None:
        args.inkscape = getenv("REPREP_INKSCAPE", "inkscape")
    if len(args.inkscape_args) == 0:
        inkscape_args = getenv(f"REPREP_INKSCAPE_{path_out.suffix[1:].upper()}_ARGS", "")
    else:
        inkscape_args = " ".join(args.inkscape_args)
    convert_svg_pdf(args.path_svg, path_out, args.inkscape, inkscape_args, args.optional)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-convert-inkscape",
        description="Convert an SVG to PDF or PNG, with dependency tracking.",
    )
    parser.add_argument("path_svg", help="The input SVG file.")
    parser.add_argument("path_out", help="The output PDF or PNG file.")
    parser.add_argument(
        "inkscape_args",
        nargs="*",
        help="Additional arguments to be passed into inkscape. "
        "E.g. -T (for text to path conversion). "
        "Depending on the output extension, the defaults is `${REPREP_INKSCAPE_PDF_ARGS}` or "
        "`${REPREP_INKSCAPE_PDF_ARGS}`, if the environment variable is defined.",
    )
    parser.add_argument(
        "--inkscape",
        help="The inkscape executable to use. "
        "Defaults to `${REPREP_INKSCAPE}` variable or `inkscape` if the variable is unset.",
    )
    parser.add_argument(
        "--optional",
        default=False,
        action="store_true",
        help="With this option, the conversion becomes optional.",
    )
    return parser.parse_args()


def convert_svg_pdf(
    path_svg: str, path_out: Path, inkscape: str, inkscape_args: str, optional: bool
):
    inp_paths = search_svg_deps(path_svg)
    ffmt = path_out.suffix[1:]
    step(
        f"SELF_CALL=x {inkscape} {path_svg} {inkscape_args} "
        f"--export-filename={path_out} --export-type={ffmt}",
        inp=[path_svg, *inp_paths],
        out=path_out,
        optional=optional,
    )


RE_OPTIONS = re.MULTILINE | re.DOTALL
RE_SVG_HREF = re.compile(rb"<image\s[^<]*?href=\"(?!#)(?!data:)(.*?)\"[^<]*?>", RE_OPTIONS)


def search_svg_deps(src: str) -> list[str]:
    """Search implicit dependencies in SVG files, specifically (recursively) included images."""
    implicit = []
    todo = [src]
    idep = 0
    while idep < len(todo):
        path_svg = Path(todo[idep])
        # It is generally a poor practice to parse XML with a regular expression,
        # unless performance becomes an issue...
        with open(path_svg, "rb") as fh:
            hrefs = re.findall(RE_SVG_HREF, fh.read())

        # Process hrefs
        for href in hrefs:
            href = href.decode("utf-8")
            if href.startswith("file://"):
                href = href[7:]
            if "://" not in href:
                if not href.startswith("/"):
                    href = path_svg.parent / href
                implicit.append(href)
                if href.endswith(".svg"):
                    todo.append(href)
        idep += 1
    return implicit


if __name__ == "__main__":
    sys.exit(main())
