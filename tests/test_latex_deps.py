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
"""Unit tests for stepup.reprep.latex_deps"""

from stepup.reprep.latex_deps import scan_latex_deps

SCAN_LATEX_DEPS_EXAMPLE = r"""
%REPREP vol volatile.txt
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
%REPREP inp implicit.txt
%\input{bar.tex}
\bibliography {references}
%\bibliography{old}
\bibliography {
    extra}
\import  {sub  % poor formatting
}    {inc.tex
}
%import{sub}{ex.tex}
%REPREP out sideffect.txt
"""


def test_scan_latex_deps(monkeypatch, path_tmp):
    monkeypatch.chdir(path_tmp)
    with open("main.tex", "w") as fh:
        fh.write(SCAN_LATEX_DEPS_EXAMPLE)
    inp, bib, out, vol = scan_latex_deps("main.tex", "./")
    inp_ref = {
        "foo.tex",
        "results/info.tex",
        "this also works.tex",
        "figure.pdf",
        "plot.pdf",
        "implicit.txt",
        "sub/inc.tex",
    }
    assert set(inp) == inp_ref
    bib_ref = {"references.bib", "extra.bib"}
    assert set(bib) == bib_ref
    assert out == ["sideffect.txt"]
    assert vol == ["volatile.txt"]
