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
"""Markdown to HTML conversion."""

import argparse
import re
import sys
from xml.etree.ElementTree import tostring as dumps_xml

import markdown
from defusedxml.ElementTree import fromstring as loads_xml
from path import Path

from stepup.core.api import amend

from .render import render

__all__ = ("convert_markdown", "isolate_header")


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if not args.markdown.endswith(".md"):
        raise ValueError("The markdown file must end with the .md extension.")
    with open(args.markdown) as fm, open(args.html, "w") as fh:
        fh.write(
            convert_markdown(fm.read(), args.katex, args.katex_macros, args.css, args.html.parent)
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-convert-markdown", description="Convert Markdown to HTML"
    )
    parser.add_argument("markdown", type=Path, help="A Markdown file with extension `.md`")
    parser.add_argument("html", type=Path, help="A HTML output filename")
    parser.add_argument("--katex", default=False, action="store_true", help="Enable KaTeX")
    parser.add_argument("--katex-macros", type=Path, default=None, help="KaTeX macro file")
    parser.add_argument(
        "--css",
        type=Path,
        nargs="+",
        default=[],
        help="Local CSS files to link to in the HTML header",
    )
    return parser.parse_args(argv)


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  <title>{{ title }}</title>
  {{ css | indent(width=2) }}
  {{ extra_header | indent(width=2) }}
</head>
<body>
  {{ body | indent(width=2) }}
</body>
</html>
"""


def convert_markdown(
    text_md: str,
    katex: bool = False,
    path_macro: str | None = None,
    paths_css: str | list[str] | None = None,
    parent_html: str = "./",
) -> str:
    """Convert Markdown to HTML with KaTeX support.

    Parameters
    ----------
    text_md
        The markdown source text.
    katex
        Set to `True` to enable KaTeX support.
    path_macro
        A file with KaTeX macro definitions.
    paths_css
        Path of a local CSS file, or a list of multiple such paths,
        to be included in the HTML header.
        Note that one may also specify CSS file in the markdown header.
    parent_html
        The parent path of the HTML file.
        The CSS paths are rewritten to become relative to this parent path.

    Returns
    -------
    html
        The HTML conversion.
    """
    # Convert conventional LaTeX equation syntax to make it compatible with markdown_katex
    text_md = re.sub(r"\B\$(\S|\S[^\n\r]*?\S)\$\B", r"$`\1`$", text_md)

    extensions = [
        "fenced_code",
        "tables",
        "meta",
    ]
    configs = {}

    if katex:
        extensions.append("markdown_katex")
        configs["markdown_katex"] = {"insert_fonts_css": True}
        if path_macro is not None:
            configs["markdown_katex"]["macro-file"] = path_macro

    md_ctx = markdown.Markdown(
        extensions=extensions,
        extension_configs=configs,
    )

    # Convert to HTML
    body = md_ctx.convert(text_md)

    # Collect all CSS paths
    if paths_css is None:
        paths_css = []
    elif isinstance(paths_css, str):
        paths_css = [paths_css]
    paths_css.extend(md_ctx.Meta.get("css", []))
    amend(inp=[path_css for path_css in md_ctx.Meta.get("css", []) if "://" not in path_css])

    # Rewrite CSS paths is paths relative to the parent of the HTML output.
    # parent_html = Path(parent_html)
    for i, path_css in enumerate(paths_css):
        if "://" not in path_css:
            paths_css[i] = Path(path_css).relpath(parent_html)

    # When using katex, split of the header-related tags,
    # so they can be included in the header instead of the body.
    extra_header, body = isolate_header(body)

    # Use Jinja to finalize the HTML page.
    variables = {
        "body": body,
        "extra_header": extra_header,
        "title": md_ctx.Meta.get("title", ["Untitled"])[0],
        "css": "\n".join(f'<link rel="stylesheet" href="{path_css}" />' for path_css in paths_css),
    }
    return render("HTML_TEMPLATE", variables, str_in=HTML_TEMPLATE)


def isolate_header(body: str) -> tuple[str, str]:
    """Isolate HTML elements that should be put in the HTML header.

    Normally, the markdown library only produces a HTML body,
    but the markdown_katex plugin needs to insert header elements
    to format the equations correctly.
    This function isolates such header elements,
    so they can be inserted in the right part of the HTML file.

    Parameters
    ----------
    body
        A HTML body with a few header elements.

    Returns
    -------
    header
        A string with HTML header elements.
    body
        The given body without the header elements.
    """
    root = loads_xml(f'<?xml version="1.0"?><body>{body}</body>')
    header_lines = []
    body_lines = []
    for child in root:
        line = dumps_xml(child).decode("utf-8").strip()
        if len(line) > 0:
            if child.tag in ["link", "style", "meta", "title"]:
                header_lines.append(line)
            else:
                body_lines.append(line)
    return "\n".join(header_lines), "\n".join(body_lines)


if __name__ == "__main__":
    main(sys.argv[1:])
