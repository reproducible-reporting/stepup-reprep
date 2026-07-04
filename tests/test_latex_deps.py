# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
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
\includepdf[pages=-]{somepages.pdf}
%import{sub}{ex.tex}
%REPREP out sideffect.txt
"""


def test_scan_latex_deps(monkeypatch, path_tmp):
    monkeypatch.chdir(path_tmp)
    with open("main.tex", "w") as fh:
        fh.write(SCAN_LATEX_DEPS_EXAMPLE)
    inp, bib, out, vol = scan_latex_deps("main.tex", "./", do_amend=False)
    inp_ref = {
        "foo.tex",
        "results/info.tex",
        "this also works.tex",
        "figure.pdf",
        "plot.pdf",
        "implicit.txt",
        "sub/inc.tex",
        "somepages.pdf",
    }
    assert set(inp) == inp_ref
    bib_ref = {"references.bib", "extra.bib"}
    assert set(bib) == bib_ref
    assert out == ["sideffect.txt"]
    assert vol == ["volatile.txt"]
