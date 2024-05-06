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
r"""Recursively flatten a LaTeX file.

The following commands are expanded:

- ``\input``: standard LaTeX command
- ``\import``: like ``\input``, but capable of handling directory changes.

The following commands are rewritten to be consistent with the location of the flattened output:

- ``\includegraphics``
- ``\thebibliography``
- ``\verbatiminput``

This script is intentionally somewhat limited.
It expects that ``\input`` and ``\import`` commands are the only ones present on their line,
to avoid ambiguities. If this is not the case, the script will fail.
The script also assumes the ``\includgraphics``, ``\thebibliography`` and ``\verbatiminput``
commands are contained within a single line.
"""

import argparse
import re
import sys
import tempfile
from typing import TextIO

from path import Path


def main() -> int:
    """Main program."""
    args = parse_args()
    with tempfile.TemporaryDirectory("reprep-latex-flat") as tmpdir:
        tmpdir = Path(tmpdir)
        path_flat_tmp = tmpdir / "flat.tex"
        with open(path_flat_tmp, "w") as fh_out:
            out_root = Path(args.path_flat).parent
            result, inp_paths = flatten_latex(args.path_tex, fh_out, out_root)
        if len(inp_paths) > 0:
            from stepup.core.api import amend

            amend(inp=inp_paths)
        if result == 0:
            path_flat_tmp.copy(args.path_flat)
    return result


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-latex-flat",
        description="Flatten input and import commands in a LaTeX file.",
    )
    parser.add_argument("path_tex", help="The top-level tex file.")
    parser.add_argument("path_flat", help="The flattened output tex file.")
    return parser.parse_args()


def flatten_latex(
    path_tex: str, fh_out: TextIO, out_root: str, tex_root: str | None = None
) -> tuple[int, list[str]]:
    """Write a flattened LaTeX file

    Parameters
    ----------
    path_tex
        The LaTeX source to be flattened, may be the main file or
        an included file in one of the recursions.
    fh_out
        The file object to write the flattened file to.
    out_root
        The directory of the output file, needed to fix relative paths.
    tex_root
        The directory with respect to which paths in the LaTeX source must
        be interpreted.

    Returns
    -------
    returncode
        Zero when successful.
    inp_paths
        A list of additional inputs used.
    """
    inp_paths = []
    path_tex = Path(path_tex)
    tex_root = path_tex.parent.normpath() if tex_root is None else Path(tex_root)
    with open(path_tex) as fh:
        for iline, line in enumerate(fh):
            # Reduce line to standard form
            stripped = line[: line.find("%")].strip()
            stripped = stripped.replace(" ", "").replace("\t", "")

            # Try to find input or import
            status = 0
            sub_path_tex = None
            new_root = tex_root
            if r"\input{" in stripped:
                if stripped.startswith(r"\input{") and stripped.endswith("}"):
                    sub_path_tex = tex_root / stripped[7:-1]
                    if not sub_path_tex.endswith(".tex"):
                        sub_path_tex = sub_path_tex.with_suffix(".tex")
                    if not sub_path_tex.is_file():
                        status = -1
                else:
                    status = -2
            elif r"\import{" in stripped:
                if stripped.startswith(r"\import{") and "}{" in stripped and stripped.endswith("}"):
                    new_root, sub_path_tex = stripped[8:-1].split("}{")
                    new_root = (tex_root / new_root).normpath()
                    sub_path_tex = new_root / sub_path_tex
                    if not sub_path_tex.endswith(".tex"):
                        sub_path_tex = sub_path_tex.with_suffix(".tex")
                    if not sub_path_tex.is_file():
                        status = -1
                else:
                    status = -2

            # Handle result
            if isinstance(sub_path_tex, str):
                inp_paths.append(sub_path_tex)
            if status < 0:
                if status == -1:
                    print(
                        f"Could not locate input file '{sub_path_tex}' "
                        f"on line {iline+1} in '{path_tex}'",
                        file=sys.stderr,
                    )
                elif status == -2:
                    print(
                        f"Could not parse '{stripped}' on line {iline+1} in '{path_tex}'",
                        file=sys.stderr,
                    )
                else:
                    print("Unknown error", file=sys.stderr)
                break
            elif isinstance(sub_path_tex, str):
                status, sub_inp_paths = flatten_latex(sub_path_tex, fh_out, out_root, new_root)
                inp_paths.extend(sub_inp_paths)
                if status != 0:
                    break
            else:
                fh_out.write(rewrite_line(line, tex_root, out_root))
    return status, inp_paths


RE_REWRITE = re.compile(
    r"(?P<comopt>\\(?:includegraphics|thebibliography|verbatiminput)"
    r"(?:\s*\[.*?])?\s*)\{(?P<path>.*?)}"
)


def rewrite_line(line: str, tex_root: Path, out_root: Path) -> str:
    """Rewrite the path in a source line.

    Parameters
    ----------
    line
        A line of LaTeX source code, possibly containing ``\\includegraphics``
        or ``\\thebibliography`` commands that need fixing.
    tex_root
        The directory with respect to which paths in the LaTeX source should
        be interpreted.
    out_root
        The new directory, with respect to which paths in the rewritten
        LaTeX source must be interpreted.

    Returns
    -------
    fixed_line
        A line in which the paths are fixed.
    """

    def repl(m):
        old_path = m.group("path")
        new_path = (tex_root / old_path).relpath(out_root).normpath()
        return m.group("comopt") + "{" + new_path + "}"

    return RE_REWRITE.sub(repl, line)


if __name__ == "__main__":
    sys.exit(main())
