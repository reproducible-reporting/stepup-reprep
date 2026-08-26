# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Markdown to HTML conversion."""

import argparse
from collections.abc import Collection, Sequence

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from path import Path

from stepup.core.api import amend, getenv
from stepup.core.render_jinja import render_jinja_str

__all__ = ("convert_markdown", "main")


def main(argv: Sequence[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if not args.markdown.endswith(".md"):
        raise ValueError("The markdown file must end with the .md extension.")
    if len(args.css) == 0:
        args.css = getenv("REPREP_MARKDOWN_CSS", multi=True, back=True)
    with open(args.markdown) as fm, open(args.html, "w") as fh:
        fh.write(convert_markdown(fm.read(), args.css, args.html.parent))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-convert-markdown", description="Convert Markdown to HTML"
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

    tokens = md.parse(text_md)
    body = md.renderer.render(tokens, md.options, {})
    meta = {}
    if tokens[0].type == "front_matter":
        meta = yaml.safe_load(tokens[0].content)

    parent_html = Path(parent_html)
    paths_doc_css = meta.get("css", [])
    if isinstance(paths_doc_css, str):
        paths_doc_css = [paths_doc_css]
    amend(inp=[parent_html / path_css for path_css in paths_doc_css if "://" not in path_css])

    if isinstance(paths_css, str):
        paths_css = paths_css.split(":")
    paths_css = [
        Path(path_css).relpath(parent_html) for path_css in paths_css if "://" not in path_css
    ]
    paths_css.extend(paths_doc_css)

    variables = {
        "body": body,
        "title": meta.get("title", "Untitled"),
        "css": "\n".join(f'<link rel="stylesheet" href="{path_css}" />' for path_css in paths_css),
    }
    return render_jinja_str(HTML_TEMPLATE, variables, name="HTML_TEMPLATE")


if __name__ == "__main__":
    main()
