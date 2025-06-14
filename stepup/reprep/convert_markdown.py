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
"""Markdown to HTML conversion."""

import argparse
import sys
from collections.abc import Collection

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from path import Path

from stepup.core.api import amend, getenv
from stepup.core.render_jinja import render_jinja

__all__ = ("convert_markdown",)


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if not args.markdown.endswith(".md"):
        raise ValueError("The markdown file must end with the .md extension.")
    if len(args.css) == 0:
        args.css = getenv("REPREP_MARKDOWN_CSS", multi=True, back=True)
    with open(args.markdown) as fm, open(args.html, "w") as fh:
        fh.write(convert_markdown(fm.read(), args.css, args.html.parent))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-convert-markdown", description="Convert Markdown to HTML"
    )
    parser.add_argument("markdown", type=Path, help="A Markdown file with extension `.md`")
    parser.add_argument("html", type=Path, help="A HTML output filename")
    parser.add_argument(
        "--css",
        type=Path,
        nargs="+",
        default=(),
        help="Local CSS files to link to in the HTML header. "
        "The default value is ${REPREP_MARKDOWN_CSS} (if defined) "
        "and it is interpreted as a colon-separated list.",
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
</head>
<body>
  {{ body | indent(width=2) }}
</body>
</html>
"""


def convert_markdown(
    text_md: str,
    paths_css: str | Collection[str] = (),
    parent_html: str = "./",
) -> str:
    """Convert Markdown to HTML.

    Parameters
    ----------
    text_md
        The markdown source text.
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
    md = MarkdownIt().use(front_matter_plugin).use(anchors_plugin)

    # Convert to HTML and get front matter.
    tokens = md.parse(text_md)
    body = md.renderer.render(tokens, md.options, {})
    meta = {}
    if tokens[0].type == "front_matter":
        meta = yaml.safe_load(tokens[0].content)

    # Collect CSS paths from the source and amend them
    parent_html = Path(parent_html)
    paths_doc_css = meta.get("css", [])
    if isinstance(paths_doc_css, str):
        paths_doc_css = [paths_doc_css]
    amend(inp=[parent_html / path_css for path_css in paths_doc_css if "://" not in path_css])

    # Convert the given CSS files to be relative to the parent of the HTML file.
    if isinstance(paths_css, str):
        paths_css = paths_css.split(":")
    paths_css = [
        Path(path_css).relpath(parent_html) for path_css in paths_css if "://" not in path_css
    ]
    paths_css.extend(paths_doc_css)

    # Use Jinja to finalize the HTML page.
    variables = {
        "body": body,
        "title": meta.get("title", "Untitled"),
        "css": "\n".join(f'<link rel="stylesheet" href="{path_css}" />' for path_css in paths_css),
    }
    return render_jinja("HTML_TEMPLATE", variables, str_in=HTML_TEMPLATE)


if __name__ == "__main__":
    main(sys.argv[1:])
