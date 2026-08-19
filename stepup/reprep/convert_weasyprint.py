# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Wrapper for HTML to PDF conversion."""

import argparse
import shlex
from collections.abc import Iterator

from defusedxml import ElementTree
from path import Path

from stepup.core.api import amend, getenv
from stepup.core.extapi import run_subprocess

__all__ = ("main",)


def main():
    """Main program."""
    args = parse_args()
    if not args.path_pdf.endswith(".pdf"):
        raise ValueError("The output must have a pdf extensions.")
    if args.weasyprint is None:
        args.weasyprint = getenv("REPREP_WEASYPRINT", "weasyprint")
    inp_paths = search_html_deps(args.path_html)
    amend(inp=inp_paths)
    popenargs = [args.weasyprint, args.path_html, args.path_pdf]
    run_subprocess(shlex.join(popenargs))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-convert-weasyprint",
        description="Convert a HTML to PDF, with dependency tracking.",
    )
    parser.add_argument("path_html", help="The input HTML file.")
    parser.add_argument("path_pdf", help="The output PDF file.")
    parser.add_argument(
        "--weasyprint",
        help="The weasyprint executable to use. "
        "Defaults to `${REPREP_WEASYPRINT}` variable or `weasyprint` if the variable is unset.",
    )
    return parser.parse_args()


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
    main()
