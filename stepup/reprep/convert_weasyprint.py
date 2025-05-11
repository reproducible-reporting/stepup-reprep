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
"""Wrapper for HTML to PDF conversion."""

import argparse
import shlex
import sys
from collections.abc import Iterator

from defusedxml import ElementTree
from path import Path

from stepup.core.api import amend, getenv
from stepup.core.worker import WorkThread


def main(argv: list[str] | None = None, work_thread: WorkThread | None = None):
    """Main program."""
    args = parse_args(argv)
    if work_thread is None:
        work_thread = WorkThread("stub")

    if not args.path_pdf.endswith(".pdf"):
        raise ValueError("The output must have a pdf extensions.")
    if args.weasyprint is None:
        args.weasyprint = getenv("REPREP_WEASYPRINT", "weasyprint")
    inp_paths = search_html_deps(args.path_html)
    amend(inp=inp_paths)
    popenargs = [args.weasyprint, args.path_html, args.path_pdf]
    returncode = work_thread.runsh_verbose(shlex.join(popenargs))
    if returncode != 0:
        sys.exit(returncode)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-convert-weasyprint",
        description="Convert a HTML to PDF, with dependency tracking.",
    )
    parser.add_argument("path_html", help="The input HTML file.")
    parser.add_argument("path_pdf", help="The output PDF file.")
    parser.add_argument(
        "--weasyprint",
        help="The weasyprint executable to use. "
        "Defaults to `${REPREP_WEASYPRINT}` variable or `weasyprint` if the variable is unset.",
    )
    return parser.parse_args(argv)


def search_html_deps(src: str) -> list[str]:
    """Search implicit dependencies in HTML files: included images and css."""
    implicit = []
    todo = [src]
    idep = 0
    while idep < len(todo):
        path_html = Path(todo[idep])
        for href in iter_html_hrefs(path_html):
            if href.startswith("file://"):
                href = href[7:]
            if "://" not in href:
                if not href.startswith("/"):
                    href = path_html.parent / href
                implicit.append(href)
                if href.endswith(".html"):
                    todo.append(href)
        idep += 1
    return implicit


def iter_html_hrefs(path_html: str) -> Iterator[str]:
    parser = ElementTree.iterparse(path_html, events=("start",))
    for event, elem in parser:
        if event == "start":
            tag = elem.tag.rpartition("}")[2]
            if tag == "img":
                for key in "src", "{http://www.w3.org/1999/xhtml}src":
                    href = elem.attrib.get(key)
                    if href is not None and "data:image" not in href:
                        yield href
                        break
            elif tag == "link":
                for key in "href", "{http://www.w3.org/1999/xhtml}href":
                    href = elem.attrib.get(key)
                    if href is not None and "data:image" not in href:
                        yield href
                        break
        elem.clear()


if __name__ == "__main__":
    main(sys.argv[1:])
