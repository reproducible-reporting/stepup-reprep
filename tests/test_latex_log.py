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
"""Unit tests for stepup.reprep.latex_log"""

import pytest
from reprep_common import local_file

from stepup.reprep.latex_log import (
    DEFAULT_MESSAGE,
    MESSAGE_SUFFIX,
    LatexSourceStack,
    parse_latex_log,
)

LATEX_LOG1 = r"""
**article
(./article.tex
LaTeX2e <2022-06-01> patch level 5

[17] [18] [19]
<fig1.pdf, id=90, 200pt x 200pt>
File: fig1.pdf Graphic file (type pdf)
<use fig1.pdf>
Package pdftex.def Info: fig1.pdf  used on input line 300.
(pdftex.def)             Requested size:  200pt x 200pt.
[20] [21]
! Undefined control sequence.
l.396         \begin{center}\foo

The control sequence at the end of the top line
of your error message was never \def'ed. If you have
misspelled it (e.g., `\hobx'), type `I' and the correct
spelling (e.g., `I\hbox'). Otherwise just continue,
and I'll forget about whatever was undefined.

<fig2.pdf, id=97, 100pt x 100pt>
File: fig2.pdf Graphic file (type pdf)
<use fig2.pdf>
"""

LATEX_LOG1_MESSAGE = r"""
! Undefined control sequence.
l.396         \begin{center}\foo
"""


def test_parse_latex_log1(tmpdir):
    with local_file(LATEX_LOG1, "article.log", tmpdir):
        error_info = parse_latex_log("article.log")
    assert error_info.program == "LaTeX"
    assert error_info.src == "./article.tex"
    assert (
        error_info.message.strip()
        == (LATEX_LOG1_MESSAGE + MESSAGE_SUFFIX.format(path="article.log")).strip()
    )


LATEX_LOG2 = r"""
not so much
"""


def test_parse_latex_log2(tmpdir):
    with local_file(LATEX_LOG2, "article.log", tmpdir):
        error_info = parse_latex_log("article.log")
    assert error_info.program == "LaTeX"
    assert error_info.src == "(could not detect source file)"
    assert error_info.message == DEFAULT_MESSAGE.format(path="article.log")


LATEX_LOG3 = r"""
LaTeX Font Info:    Font shape `T1/mdput/m/sl' will be
(Font)              scaled to size 11.28003pt on input line 24.
[1

] (./kwart_cirkelboog_e/divergent.inc.tex

! LaTeX Error: Something's wrong--perhaps a missing \item.

See the LaTeX manual or LaTeX Companion for explanation.
Type  H <return>  for immediate help.
 ...

l.2 \item E
           lektrisch veld opgewekt door continue ladingsverdeling: $\vec{E} ...

Try typing  <return>  to proceed.
If that doesn't work, type  X <return>  to quit.

LaTeX Font Info:    Font shape `OML/mdput/b/n' will be
(Font)              scaled to size 11.28003pt on input line 2.
LaTeX Font Info:    Font shape `OML/mdput/b/n' will be
(Font)              scaled to size 7.52002pt on input line 2.
"""


LATEX_LOG3_MESSAGE = r"""
! LaTeX Error: Something's wrong--perhaps a missing \item.

l.2 \item E
           lektrisch veld opgewekt door continue ladingsverdeling: $\vec{E} ...
"""


def test_parse_latex_log3(tmpdir):
    with local_file(LATEX_LOG3, "article.log", tmpdir):
        error_info = parse_latex_log("article.log")
    assert error_info.program == "LaTeX"
    assert error_info.src == "./kwart_cirkelboog_e/divergent.inc.tex"
    assert (
        error_info.message.strip()
        == (LATEX_LOG3_MESSAGE + MESSAGE_SUFFIX.format(path="article.log")).strip()
    )


LATEX_LOG4 = r"""
**foo
] (./review.tex

(/usr/share/texlive/texmf-dist/tex/latex/mathdesign/mdttfont.def
)

Package hyperref Info: Link coloring ON on input line 29.
(./review.out) (./review.out)
\@outlinefile=\write4
\openout4 = `review.out'.

! Missing $ inserted.
<inserted text>
                $
l.116 \end{gather*}

I've inserted a begin-math/end-math symbol since I think
you left one out. Proceed, with fingers crossed.

LaTeX Font Info:    Font shape `T1/mdput/m/n' will be
(Font)              scaled to size 4.70001pt on input line 116.
! Extra }, or forgotten $.
<template> }
            }\savetaglength@ \endtemplate
l.116 \end{gather*}

I've deleted a group-closing symbol because it seems to be
spurious, as in `$x}$'. But perhaps the } is legitimate and
you forgot something else, as in `\hbox{$x}'. In such cases
the way to recover is to insert both the forgotten and the
deleted material, e.g., by typing `I$}'.

! Extra }, or forgotten $.
<template> }}
             \savetaglength@ \endtemplate
l.116 \end{gather*}

I've deleted a group-closing symbol because it seems to be
spurious, as in `$x}$'. But perhaps the } is legitimate and
you forgot something else, as in `\hbox{$x}'. In such cases
the way to recover is to insert both the forgotten and the
deleted material, e.g., by typing `I$}'.

! Missing $ inserted.
<inserted text>
                $
l.116 \end{gather*}

I've inserted a begin-math/end-math symbol since I think
you left one out. Proceed, with fingers crossed.
"""

LATEX_LOG4_MESSAGE = r"""
! Missing $ inserted.
<inserted text>
                $
l.116 \end{gather*}
"""


def test_parse_latex_log4(tmpdir):
    with local_file(LATEX_LOG4, "article.log", tmpdir):
        error_info = parse_latex_log("article.log")
    assert error_info.program == "LaTeX"
    assert error_info.src == "./review.tex"
    assert (
        error_info.message.strip()
        == (LATEX_LOG4_MESSAGE + MESSAGE_SUFFIX.format(path="article.log")).strip()
    )


LATEX_LOG5 = r"""
This is XeTeX, Version 3.141592653-2.6-0.999994 (TeX Live 2022/CVE-2023-32700 patched)
entering extended mode
 restricted \write18 enabled.
 %&-line parsing enabled.
**solutions
(./solutions.tex
LaTeX2e <2022-06-01> patch level 5
L3 programming layer <2022-12-17> (/usr/share/texlive/texmf-dist/tex/latex/base
/article.cls
Document Class: article 2021/10/04 v1.4n Standard LaTeX document class
(/usr/share/texlive/texmf-dist/tex/latex/base/size12.clo
File: size12.clo 2021/10/04 v1.4n Standard LaTeX file (size option)
)
\bibindent=\dimen140
) (../../../../preamble.inc.tex (/usr/share/texlive/texmf-dist/tex/latex/mathde
sign/mathdesign.sty
))

[1

] (./example/solution.inc.tex
LaTeX Font Info:    Font shape `T1/mdput/m/n' will be
(Font)              scaled to size 7.52002pt on input line 5.
LaTeX Font Info:    Font shape `T1/mdput/m/n' will be
(Font)              scaled to size 4.70001pt on input line 5.
)

! LaTeX Error: Something's wrong--perhaps a missing \item.

See the LaTeX manual or LaTeX Companion for explanation.
Type  H <return>  for immediate help.
 ...

l.40 \end{enumerate}

Try typing  <return>  to proceed.
If that doesn't work, type  X <return>  to quit.
"""

LATEX_LOG5_MESSAGE = r"""
! LaTeX Error: Something's wrong--perhaps a missing \item.

l.40 \end{enumerate}
"""


def test_parse_latex_log5(tmpdir):
    with local_file(LATEX_LOG5, "article.log", tmpdir):
        error_info = parse_latex_log("article.log")
    assert error_info.program == "LaTeX"
    assert error_info.src == "./solutions.tex"
    assert (
        error_info.message.strip()
        == (LATEX_LOG5_MESSAGE + MESSAGE_SUFFIX.format(path="article.log")).strip()
    )


def check_source_stack(latex_log, nline, stack, unfinished):
    lines = latex_log.split("\n")[:nline]
    lss = LatexSourceStack()
    for line in lines:
        lss.feed(line + "\n")
    assert lss.stack == stack
    assert lss.unfinished == unfinished
    assert not lss.unmatched


@pytest.mark.parametrize(
    ("nline", "stack", "unfinished"),
    [
        (7, ["./solutions.tex"], None),
        (
            9,
            ["./solutions.tex"],
            "L3 programming layer <2022-12-17> (/usr/share/texlive/texmf-dist/tex/latex/base",
        ),
        (
            10,
            [
                "./solutions.tex",
                "/usr/share/texlive/texmf-dist/tex/latex/base/article.cls",
            ],
            None,
        ),
        (
            16,
            [
                "./solutions.tex",
                "/usr/share/texlive/texmf-dist/tex/latex/base/article.cls",
            ],
            ") (../../../../preamble.inc.tex (/usr/share/texlive/texmf-dist/tex/latex/mathde",
        ),
        (
            17,
            [
                "./solutions.tex",
                "../../../../preamble.inc.tex",
                "/usr/share/texlive/texmf-dist/tex/latex/mathdesign/mathdesign.sty",
            ],
            None,
        ),
        (18, ["./solutions.tex"], None),
        (24, ["./solutions.tex", "./example/solution.inc.tex"], None),
        (30, ["./solutions.tex"], None),
    ],
)
def test_latex_source_stack5(nline, stack, unfinished):
    check_source_stack(LATEX_LOG5, nline, stack, unfinished)


LATEX_LOG6 = r"""
This is XeTeX, Version 3.141592653-2.6-0.999994 (TeX Live 2022/CVE-2023-32700 patched)
entering extended mode
 restricted \write18 enabled.
 %&-line parsing enabled.
**review
(./review.tex

[5] (./weerstand_serie_en_parallel2/method.inc.tex) (./weerstand_serie_en_paral
lel2/answer.inc.tex)
Overfull \hbox (6.20514pt too wide) in paragraph at lines 315--336
\T1/mdput/m/n/12 -  []
 []

(./weerstand_serie_en_parallel2/solution.inc.tex
File: weerstand_serie_en_parallel2//stappen12.pdf Graphic file (type pdf)
<use weerstand_serie_en_parallel2//stappen12.pdf>
[6]
File: weerstand_serie_en_parallel2//stappen34.pdf Graphic file (type pdf)
<use weerstand_serie_en_parallel2//stappen34.pdf>
) (./interactie_eindige_dipolen/stem.inc.tex
File: interactie_eindige_dipolen//paar_dipolen.pdf Graphic file (type pdf)
<use interactie_eindige_dipolen//paar_dipolen.pdf>
) [7] (./interactie_eindige_dipolen/validation.inc.tex)
! Missing $ inserted.
<inserted text>
                $
l.355

I've inserted something that you may have forgotten.
(See the <inserted text> above.)
With luck, this will get me unwedged. But if you
really didn't forget anything, try typing `2' now; then
my insertion and my current dilemma will both disappear.
"""

LATEX_LOG6_MESSAGE = r"""
! Missing $ inserted.
<inserted text>
                $
l.355
"""


def test_parse_latex_log6(tmpdir):
    with local_file(LATEX_LOG6, "article.log", tmpdir):
        error_info = parse_latex_log("article.log")
    assert error_info.program == "LaTeX"
    assert error_info.src == "./review.tex"
    assert (
        error_info.message.strip()
        == (LATEX_LOG6_MESSAGE + MESSAGE_SUFFIX.format(path="article.log")).strip()
    )


LATEX_LOG7 = r"""
(./pdftexcmds.sty
Package: pdftexcmds 2020-06-27 v0.33 Utility functions of pdfTeX for LuaTeX (HO
)
(./infwarerr.sty
Package: infwarerr 2019/12/03 v1.5 Providing info/warning/error messages (HO)
)
)
"""


@pytest.mark.parametrize(
    ("nline", "stack", "unfinished"),
    [
        (2, ["./pdftexcmds.sty"], None),
        (
            3,
            ["./pdftexcmds.sty"],
            "Package: pdftexcmds 2020-06-27 v0.33 Utility functions of pdfTeX for LuaTeX (HO",
        ),
        (4, ["./pdftexcmds.sty"], None),
        (5, ["./pdftexcmds.sty", "./infwarerr.sty"], None),
        (6, ["./pdftexcmds.sty", "./infwarerr.sty"], None),
        (7, ["./pdftexcmds.sty"], None),
        (8, [], None),
    ],
)
def test_latex_source_stack7(nline, stack, unfinished):
    check_source_stack(LATEX_LOG7, nline, stack, unfinished)


LATEX_LOG8 = r"""
(/usr/share/texlive/texmf-dist/tex/generic/pgf/basiclayer/pgfcorequick.code.tex
File: pgfcorequick.code.tex 2021/05/15 v3.1.9a (3.1.9a)
)
"""


@pytest.mark.parametrize(
    ("nline", "stack", "unfinished"),
    [
        (
            3,
            ["/usr/share/texlive/texmf-dist/tex/generic/pgf/basiclayer/pgfcorequick.code.tex"],
            None,
        ),
    ],
)
def test_latex_source_stack8(nline, stack, unfinished):
    check_source_stack(LATEX_LOG8, nline, stack, unfinished)


LATEX_LOG9 = r"""
(./first.tex
Bluh
(./second.tex))
Blah
"""


@pytest.mark.parametrize(
    ("nline", "stack", "unfinished"),
    [
        (2, ["./first.tex"], None),
        (3, ["./first.tex"], None),
        (4, [], None),
        (5, [], None),
    ],
)
def test_latex_source_stack9(nline, stack, unfinished):
    check_source_stack(LATEX_LOG9, nline, stack, unfinished)


LATEX_LOG10 = r"""
This is XeTeX, Version 3.141592653-2.6-0.999995 (TeX Live 2023)
(preloaded format=xelatex 2023.12.26)  14 JAN 2024 10:12
entering extended mode
 restricted \write18 enabled.
 %&-line parsing enabled.
**questions
(./questions.tex
LaTeX2e <2022-11-01> patch level 1
L3 programming layer <2023-02-22>
(/usr/share/texlive/texmf-dist/tex/latex/base/article.cls
Document Class: article 2022/07/02 v1.4n Standard LaTeX document class
(/usr/share/texlive/texmf-dist/tex/latex/base/size12.clo
File: size12.clo 2022/07/02 v1.4n Standard LaTeX file (size option)
))

LaTeX Warning: File `20.png' not found on input line 549.

! Unable to load picture or PDF file '20.png'.
<to be read again>
                   }
l.549     \answergrid

?
! Emergency stop.
<to be read again>
"""

LATEX_LOG10_MESSAGE = r"""
! Unable to load picture or PDF file '20.png'.
<to be read again>
                   }
l.549     \answergrid
"""


def test_parse_latex_log10(tmpdir):
    with local_file(LATEX_LOG10, "questions.log", tmpdir):
        error_info = parse_latex_log("questions.log")
    assert error_info.program == "LaTeX"
    assert error_info.src == "./questions.tex"
    print(error_info.message.strip())
    print("####")
    print((LATEX_LOG10_MESSAGE + MESSAGE_SUFFIX.format(path="questions.log")).strip())
    assert (
        error_info.message.strip()
        == (LATEX_LOG10_MESSAGE + MESSAGE_SUFFIX.format(path="questions.log")).strip()
    )
