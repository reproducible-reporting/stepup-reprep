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
"""Minimalistic bibtex parser.

Known limitations (by design) to keep things simple:

- No support for @preamble entries.
- No support for string concatenation with #.
- No support for string definitions with @string.
- No support for comments with @comment.
- No special handling of LaTeX commands or special characters.
- Overwrites fields __KEY__ and __ETYPE__ if present in the BibTeX entry.
"""

from importlib import resources

from lark import Lark, Token, Transformer
from lark.exceptions import LarkError

__all__ = ("BibtexParseError", "format_bib", "parse_bib")


class BibtexParseError(RuntimeError):
    pass


class BibTransformer(Transformer):
    def start(self, items):
        return [x for x in items if isinstance(x, dict)]

    def entry(self, items):
        items = [item for item in items if not isinstance(item, Token)]
        etype, key, fields = items
        if fields is None:
            fields = {}
        entry = dict(fields)
        entry["__ETYPE__"] = str(etype)
        entry["__KEY__"] = str(key)
        return entry

    def entry_type(self, items):
        return str(items[0]).lower()

    def key(self, items):
        return str(items[0])

    def field_list(self, items):
        out = None
        for item in items:
            if isinstance(item, dict):
                out = item
            elif isinstance(item, tuple) and len(item) == 2:
                if out is None:
                    out = {}
                k, v = item
                out[str(k)] = str(v)
        return out

    def field(self, items):
        return str(items[0]).lower(), str(items[-1])

    def value(self, items):
        result = items[0]
        if result[0] == "{" and result[-1] == "}":
            return result[1:-1]
        if result[0] == '"' and result[-1] == '"':
            return result[1:-1]
        return result

    def braced_text(self, items):
        return "".join(str(x) for x in items)

    def quoted_text(self, items):
        return "".join(str(x) for x in items)


PARSER = Lark(
    resources.files(__package__).joinpath("bibtex.lark").read_text(encoding="utf-8"),
    start="start",
    parser="lalr",
    lexer="contextual",
    # strict=True,
    # debug=True,
    transformer=BibTransformer(),
)


def parse_bib(text: str) -> list[dict]:
    try:
        return PARSER.parse(text)
    except LarkError as e:
        raise BibtexParseError(str(e)) from e


def format_bib(entries: list[dict], indent: str = " ") -> str:
    out = []
    for entry in entries:
        out.append(f"@{entry['__ETYPE__']}{{{entry['__KEY__']}")
        for key, value in sorted(entry.items()):
            if key not in ("__ETYPE__", "__KEY__"):
                out.append(f",\n{indent}{key} = {{{value}}}")
        out.append("\n}\n")
        out.append("\n")
    if out:
        out.pop()  # remove last extra newline
    return "".join(out)
