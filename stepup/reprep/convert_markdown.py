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

import markdown

from .render import render

__all__ = ("convert_markdown",)


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if not args.markdown.endswith(".md"):
        raise ValueError("The markdown file must end with the .md extension.")
    with open(args.markdown) as fm, open(args.html, "w") as fh:
        fh.write(convert_markdown(fm.read(), args.katex, args.katex_macros))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-convert-markdown", description="Convert Markdown to HTML"
    )
    parser.add_argument("markdown", help="A Markdown file with extension `.md`")
    parser.add_argument("html", help="A HTML output filename")
    parser.add_argument("--katex", default=False, action="store_true", help="Enable KaTeX")
    parser.add_argument("--katex-macros", default=None, help="KaTeX macro file")
    return parser.parse_args(argv)


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  <title>{{ title }}</title>
  {{ css | indent(width=2) }}
</head>
<body>
  {{ body | indent(width=2) }}
</body>
</html>
"""


def convert_markdown(text_md: str, katex: bool = False, path_macro: str | None = None) -> str:
    """Convert Markdown to HTML with KaTeX support.

    Parameters
    ----------
    text_md
        The markdown source text.
    katex
        Set to `True` to enable KaTeX support.
    path_macro
        A file with KaTeX macro definitions.

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
    variables = {
        "body": body,
        "title": md_ctx.Meta.get("title", ["Untitled"])[0],
        "css": "\n".join(
            f'<link rel="stylesheet" href="{path_css}" />'
            for path_css in md_ctx.Meta.get("css", [])
        ),
    }
    return render("HTML_TEMPLATE", variables, str_in=HTML_TEMPLATE)


if __name__ == "__main__":
    main(sys.argv[1:])
