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
"""Unit tests for stepup.reprep.latex_deps"""

from stepup.reprep.latex_deps import scan_latex_deps

SCAN_LATEX_DEPS_EXAMPLE = r"""
\input{foo.tex}
%\includegraphics{not.pdf}
\includegraphics{figure}
\includegraphics{\thepage.png} %REPREP ignore
\includegraphics
{plot.pdf}
\input{
    % comments before
    results/info.tex
    % comments after
}
\input  {
    % comment 1
    this
    % comment 2 }
    also
    % comment 3 {
    works % comment 4
    % comment 5 }
}
%REPREP input implicit.txt
%\input{bar.tex}
\bibliography {references}
%\bibliography{old}
\bibliography {
    extra}
\import  {sub  % poor formatting
}    {inc.tex
}
%import{sub}{ex.tex}
"""


def test_scan_latex_deps(path_tmp):
    path_main_tex = path_tmp / "main.tex"
    with open(path_main_tex, "w") as fh:
        fh.write(SCAN_LATEX_DEPS_EXAMPLE)
    implicit, bib = scan_latex_deps(path_main_tex, path_tmp)
    implicit_ref = [
        "foo.tex",
        "results/info.tex",
        "this also works.tex",
        "figure.pdf",
        "plot.pdf",
        "implicit.txt",
        "sub/inc.tex",
    ]
    implicit_ref = {path_tmp / name for name in implicit_ref}
    assert set(implicit) == implicit_ref
    bib_ref = ["references.bib", "extra.bib"]
    bib_ref = {path_tmp / name for name in bib_ref}
    assert set(bib) == bib_ref
