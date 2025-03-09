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
"""Unit tests for stepup.reprep.latex_flat"""

from stepup.reprep.flatten_latex import flatten_latex

MAIN_TEX = r"""
\begin{document}
\input{table}
\includegraphics{smile}\cite{knuth:1984}
\import{sub}{foo.tex}
\end{document}
"""

TABLE_TEX = "This is a table.\n"

FOO_TEX = r"""This is a foo.
\includegraphics[width=5cm]{smile.pdf}
\thebibliography{references}
\input{other.tex}
"""

OTHER_TEX = "Another line.\n"

EXPECTED = r"""
\begin{document}
This is a table.
\includegraphics{../smile}\cite{knuth:1984}
This is a foo.
\includegraphics[width=5cm]{../sub/smile.pdf}
\thebibliography{../sub/references}
Another line.
\end{document}
"""

CREATE_FILES = {
    "main.tex": MAIN_TEX,
    "table.tex": TABLE_TEX,
    "sub/foo.tex": FOO_TEX,
    "sub/other.tex": OTHER_TEX,
}


def test_latex_flat(path_tmp):
    for filename, contents in CREATE_FILES.items():
        path_dst = path_tmp / filename
        path_dst.parent.makedirs_p()
        with open(path_dst, "w") as fh:
            fh.write(contents)
    flatdir = path_tmp / "flat"
    flatdir.makedirs_p()
    with open(flatdir / "main.tex", "w") as fh:
        flatten_latex(path_tmp / "main.tex", fh, flatdir)
    with open(flatdir / "main.tex") as fh:
        result = fh.read()
    assert result.strip() == EXPECTED.strip()


def test_latex_flat_simple(path_tmp):
    with open(path_tmp / "main.tex", "w") as fh:
        fh.write("Not so much to see here.")
    with open(path_tmp / "flat.tex", "w") as fh:
        flatten_latex(path_tmp / "main.tex", fh, path_tmp)
    with open(path_tmp / "flat.tex") as fh:
        result = fh.read()
    assert result.strip() == "Not so much to see here."


def test_latex_flat_empty(path_tmp):
    with open(path_tmp / "main.tex", "w") as fh:
        pass
    with open(path_tmp / "flat.tex", "w") as fh:
        flatten_latex(path_tmp / "main.tex", fh, path_tmp)
    with open(path_tmp / "flat.tex") as fh:
        result = fh.read()
    assert result.strip() == ""
