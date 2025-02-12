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
"""Unit tests for stepup.reprep.bibtex_log"""

from reprep_common import local_file

from stepup.reprep.bibtex_log import DEFAULT_MESSAGE, parse_bibtex_log

BIBTEX_BLG1 = """\
This is BibTeX, Version 0.99d (TeX Live 2022/CVE-2023-32700 patched)
Capacity: max_strings=200000, hash_size=200000, hash_prime=170003
The top-level auxiliary file: article.aux
The style file: achemso.bst
Reallocated singl_function (elt_size=4) to 100 items from 50.
Database file #1: acs-article.bib
Database file #2: references.bib
I was expecting a `{' or a `('---line 12 of file references.bib
 :
 : @article{SomeAuthor1999,
(Error may have been on previous line)
I'm skipping whatever remains of this entry
achemso 2022-11-25 v3.13f
You've used 62 entries,
            2538 wiz_defined-function locations,
            1232 strings with 23159 characters,
and the built_in function-call counts, 27532 in all, are:
"""

BIBTEX_BLG1_MESSAGE = """\
I was expecting a `{' or a `('---line 12 of file references.bib
 :
 : @article{SomeAuthor1999,
(Error may have been on previous line)
I'm skipping whatever remains of this entry
"""


def test_parse_bibtex_log1(tmpdir):
    with local_file(BIBTEX_BLG1, "bibtex.blg", tmpdir):
        error_info = parse_bibtex_log("bibtex.blg")
    assert error_info.program == "BibTeX"
    assert error_info.src == "references.bib"
    assert error_info.message == BIBTEX_BLG1_MESSAGE.strip()


BIBTEX_BLG2 = """\
This is BibTeX, Version 0.99d (TeX Live 2022/CVE-2023-32700 patched)
There are not obvious problems in the log file.
"""


def test_parse_bibtex_log2(tmpdir):
    with local_file(BIBTEX_BLG2, "bibtex.blg", tmpdir):
        error_info = parse_bibtex_log("bibtex.blg")
    assert error_info.program == "BibTeX"
    assert error_info.src == "(could not detect source file)"
    assert error_info.message == DEFAULT_MESSAGE.format(path="bibtex.blg")


BIBTEX_BLG3 = r"""\
This is BibTeX, Version 0.99d (TeX Live 2023)
Capacity: max_strings=200000, hash_size=200000, hash_prime=170003
The top-level auxiliary file: reply.aux
I found no \bibstyle command---while reading file reply.aux
You've used 15 entries,
            0 wiz_defined-function locations,
            114 strings with 812 characters,
and the built_in function-call counts, 0 in all, are:
"""


def test_parse_bibtex_log3(tmpdir):
    with local_file(BIBTEX_BLG3, "bibtex.blg", tmpdir):
        error_info = parse_bibtex_log("bibtex.blg")
    assert error_info.program == "BibTeX"
    assert error_info.src == "reply.aux"
    assert error_info.message == r"I found no \bibstyle command---while reading file reply.aux"


BIBTEX_BLG4 = r"""\
This is BibTeX, Version 0.99d (TeX Live 2023)
Capacity: max_strings=200000, hash_size=200000, hash_prime=170003
The top-level auxiliary file: article.aux
The style file: achemso.bst
White space in argument---line 78 of file article.aux
 : \citation{lagauche_thermodynamic_2017
 :                                       pigeon_revisiting_2022}
I'm skipping whatever remains of this command
Reallocated singl_function (elt_size=4) to 100 items from 50.
"""


BLG_ERROR4 = """\
White space in argument---line 78 of file article.aux
 : \\citation{lagauche_thermodynamic_2017
 :                                       pigeon_revisiting_2022}
I'm skipping whatever remains of this command"""


def test_parse_bibtex_log4(tmpdir):
    with local_file(BIBTEX_BLG4, "bibtex.blg", tmpdir):
        error_info = parse_bibtex_log("bibtex.blg")
    print(error_info)
    assert error_info.program == "BibTeX"
    assert error_info.src == "article.aux"
    assert error_info.message == BLG_ERROR4
