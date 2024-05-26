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
"""Wrapper for HTML to PDF conversion."""

import argparse
import sys
from collections.abc import Iterator
from xml.etree import ElementTree

from path import Path

from stepup.core.api import getenv, step


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if not args.path_pdf.endswith(".pdf"):
        raise ValueError("The output must have a pdf extensions.")
    if args.weasyprint is None:
        args.weasyprint = getenv("REPREP_WEASYPRINT", "weasyprint")
    convert_html_pdf(args.path_html, args.path_pdf, args.weasyprint, args.optional)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-convert-weasyprint",
        description="Convert a HTML to PDF, with dependency tracking.",
    )
    parser.add_argument("path_html", help="The input HTML file.")
    parser.add_argument("path_pdf", help="The output PDF file.")
    parser.add_argument(
        "--weasyprint",
        help="The weasyprint executable to use. "
        "Defaults to `${REPREP_WEASYPRINT}` variable or `weasyprint` if the variable is unset.",
    )
    parser.add_argument(
        "--optional",
        default=False,
        action="store_true",
        help="With this option, the conversion becomes optional.",
    )
    return parser.parse_args(argv)


def convert_html_pdf(path_html: str, path_pdf: str, weasyprint: str, optional: bool):
    inp_paths = search_html_deps(path_html)
    step(
        f"{weasyprint} {path_html} {path_pdf}",
        inp=[path_html, *inp_paths],
        out=path_pdf,
        optional=optional,
    )


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
