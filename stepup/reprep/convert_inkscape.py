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
"""Wrapper for SVG to PDF conversion."""

import argparse
import os
import shlex
import sys
from collections.abc import Iterator

from defusedxml import ElementTree
from path import Path

from stepup.core.api import amend, getenv
from stepup.core.utils import filter_dependencies
from stepup.core.worker import WorkThread


def main(argv: list[str] | None = None, work_thread: WorkThread | None = None):
    """Main program."""
    args = parse_args(argv)
    if work_thread is None:
        work_thread = WorkThread("stub")

    path_out = Path(args.path_out)
    allowed_extensions = [".pdf", ".png"]
    if not any(path_out.endswith(ext) for ext in allowed_extensions):
        raise ValueError(
            f"The output must have one of the following extensions: {allowed_extensions}"
        )
    if args.inkscape is None:
        args.inkscape = getenv("REPREP_INKSCAPE", "inkscape")
    if len(args.inkscape_args) == 0:
        args.inkscape_args = shlex.split(
            getenv(f"REPREP_INKSCAPE_{path_out.suffix[1:].upper()}_ARGS", "")
        )
    inp_paths = filter_dependencies(search_svg_deps(args.path_svg))
    amend(inp=inp_paths)
    args = [
        args.inkscape,
        args.path_svg,
        *args.inkscape_args,
        f"--export-filename={path_out}",
        f"--export-type={path_out.suffix[1:]}",
    ]
    os.environ["SELF_CALL"] = "x"
    returncode = work_thread.runsh_verbose(shlex.join(args))
    if returncode != 0:
        sys.exit(returncode)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-convert-inkscape",
        description="Convert an SVG to PDF or PNG, with dependency tracking.",
    )
    parser.add_argument("path_svg", help="The input SVG file.")
    parser.add_argument("path_out", help="The output PDF or PNG file.")
    parser.add_argument(
        "inkscape_args",
        nargs="*",
        help="Additional arguments to be passed to inkscape. "
        "E.g. -T (for text to path conversion). "
        "Depending on the output extension, the defaults is `${REPREP_INKSCAPE_PDF_ARGS}` or "
        "`${REPREP_INKSCAPE_PDF_ARGS}`, if the environment variable is defined.",
    )
    parser.add_argument(
        "--inkscape",
        help="The inkscape executable to use. "
        "Defaults to `${REPREP_INKSCAPE}` variable or `inkscape` if the variable is unset.",
    )
    return parser.parse_args(argv)


def search_svg_deps(src: str) -> list[str]:
    """Search implicit dependencies in SVG files, specifically (recursively) included images."""
    implicit = []
    todo = [src]
    idep = 0
    while idep < len(todo):
        path_svg = Path(todo[idep])
        for href in iter_svg_image_hrefs(path_svg):
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


def iter_svg_image_hrefs(path_svg: str) -> Iterator[str]:
    parser = ElementTree.iterparse(path_svg, events=("start",))
    for event, elem in parser:
        if event == "start":
            tag = elem.tag.rpartition("}")[2]
            if tag == "image":
                for key in "href", "{http://www.w3.org/1999/xlink}href":
                    href = elem.attrib.get(key)
                    if href is not None and "data:image" not in href:
                        yield href
                        break
        elem.clear()


if __name__ == "__main__":
    main(sys.argv[1:])
