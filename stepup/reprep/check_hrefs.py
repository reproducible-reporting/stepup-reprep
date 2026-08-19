# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline checker for hyper references."""

import argparse
import re
import sys

import attrs
import cattrs.preconf.pyyaml
import fitz
import yaml
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from path import Path

from stepup.core.api import amend, getenv

__all__ = ("main",)


def main():
    """Main program."""
    args = parse_args()
    if args.path_config is None:
        args.path_config = getenv("REPREP_CHECK_HREFS_CONFIG", "check_hrefs.yaml", back=True)
        amend(inp=args.path_config)
    config = load_config(args.path_config)
    hrefs = collect_hrefs(args.path_src)
    make_url_substitutions(hrefs, config.subs)
    check_hrefs(hrefs, Path(args.path_src).parent.normpath(), config.accept)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-check-hrefs", description="Check hyper references Markdown, HTML or PDF files."
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
class Config:
    accept: set[str] = attrs.field(factory=set)
    subs: list[tuple[str, str]] = attrs.field(factory=list)


def load_config(path_config) -> Config:
    converter = cattrs.preconf.pyyaml.PyyamlConverter(forbid_extra_keys=True)
    with open(path_config) as fh:
        state = yaml.safe_load(fh)
        return converter.structure(state, Config)


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
    md = MarkdownIt()
    with open(fn_md) as fh:
        html = md.render(fh.read())
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


def check_hrefs(hrefs: list[HRef], root: Path, accept: set[str]):
    """Check the hyper references."""
    seen = set()
    some_failed = False
    for href in hrefs:
        if href.url in seen:
            continue
        some_failed |= check_href(href, root, accept)
        seen.add(href.url)
    if some_failed:
        raise ValueError("Some hyper references were invalid.")


def check_href(href: HRef, root: Path, accept: set[str]) -> bool:
    """Check a hyper reference and return True if an error was found."""
    if href.url.startswith("mailto:"):
        return False
    if "://" in href.translated:
        if href.translated in accept:
            return False
        print(f"FAILED LINK: {href.url}", file=sys.stderr)
        return True
    path = (root / Path(href.translated)).normpath()
    amend(inp=path)
    return False


if __name__ == "__main__":
    main()
