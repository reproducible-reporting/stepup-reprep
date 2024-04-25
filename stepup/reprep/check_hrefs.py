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
"""Offline checker for hyper references."""

import argparse
import re
import sys

import attrs
import cattrs.preconf.pyyaml
import fitz
import markdown
import yaml
from bs4 import BeautifulSoup
from path import Path

from stepup.core.api import amend, getenv
from stepup.core.utils import mynormpath


@attrs.define
class Config:
    accept: set[str] = attrs.field(factory=set)
    subs: list[tuple[str, str]] = attrs.field(factory=list)


def main() -> int:
    """Main program."""
    args = parse_args()
    if args.path_config is None:
        args.path_config = getenv("REPREP_CHECK_HREFS_CONFIG", "check_hrefs.yaml", is_path=True)
        amend(inp=args.path_config)
    config = load_config(args.path_config)
    hrefs = collect_hrefs(args.path_src)
    make_url_substitutions(hrefs, config.subs)
    return check_hrefs(hrefs, Path(args.path_src).parent.normpath(), config.accept)


def load_config(path_config) -> Config:
    converter = cattrs.preconf.pyyaml.PyyamlConverter(forbid_extra_keys=True)
    with open(path_config) as fh:
        state = yaml.safe_load(fh)
        return converter.structure(state, Config)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-check-hrefs", description="Check hyper references Markdown, HTML or PDF files."
    )
    parser.add_argument("path_src", help="Markdown, HTML or PDF file.")
    parser.add_argument(
        "-c",
        "--config",
        dest="path_config",
        help="Configuration yaml file. "
        "The default is ${REPREP_CHECK_HREFS_CONFIG} or check_hrefs.yaml if it is not set.",
    )
    return parser.parse_args()


@attrs.define
class HRef:
    """A hyper reference to be checked."""

    url: str = attrs.field()
    translated: str = attrs.field(default=None)
    ignore: bool = attrs.field(default=False, init=False)


def collect_hrefs(path_src: str) -> list[HRef]:
    """Find all hyper references in one file."""
    if path_src.endswith(".md"):
        result = collect_hrefs_md(path_src)
    elif path_src.endswith(".html"):
        result = collect_hrefs_html(path_src)
    elif path_src.endswith(".pdf"):
        result = collect_hrefs_pdf(path_src)
    else:
        raise ValueError(f"Source file type not supported: {path_src}")
    return result


def collect_hrefs_md(fn_md: str) -> list[HRef]:
    """Find all hyper references in a Markdown file."""
    with open(fn_md) as fh:
        html = markdown.markdown(fh.read())
    soup = BeautifulSoup(html, "html.parser")
    return [HRef(link.attrs["href"]) for link in soup.find_all("a")]


def collect_hrefs_html(fn_html: str) -> list[HRef]:
    """Find all hyper references in a HTML file."""
    with open(fn_html) as fh:
        soup = BeautifulSoup(fh.read(), "html.parser")
    return [HRef(link.attrs["href"]) for link in soup.find_all("a")]


def collect_hrefs_pdf(fn_pdf: str) -> list[HRef]:
    """Find all hyper references in a PDF file."""
    # See https://pymupdf.readthedocs.io/en/latest/page.html#description-of-get-links-entries
    doc = fitz.open(fn_pdf)
    hrefs = []
    for page in doc:
        for link in page.get_links():
            if link["kind"] in (fitz.LINK_LAUNCH, fitz.LINK_GOTOR):
                hrefs.append(HRef(link["file"]))
            elif link["kind"] == fitz.LINK_URI:
                hrefs.append(HRef(link["uri"]))
    return hrefs


def make_url_substitutions(hrefs: list[HRef], subs: list[tuple[str, str]]):
    for href in hrefs:
        url = href.url
        if "#" in href.url:
            url = url[: href.url.find("#")]
        for pattern, replacement in subs:
            url = re.sub(pattern, replacement, url)
        href.translated = url


def check_hrefs(hrefs: list[HRef], root: Path, accept: set[str]) -> int:
    """Check the hyper references."""
    seen = set()
    result = 0
    for href in hrefs:
        if href.url in seen:
            continue
        result |= check_href(href, root, accept)
        seen.add(href.url)
    return result


def check_href(href: HRef, root: Path, accept: set[str]) -> int:
    if href.url.startswith("mailto:"):
        return 0
    elif "://" in href.translated:
        if href.translated in accept:
            return 0
        else:
            print(f"FAILED LINK: {href.url}", file=sys.stderr)
            return 1
    path = mynormpath(root / Path(href.translated))
    amend(inp=path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
