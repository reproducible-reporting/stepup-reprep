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
"""Unit tests for stepup.reprep.bibsane"""

import contextlib
import os

import pytest
from path import Path

from stepup.reprep.bibsane import main as bibsane_main

OVERWRITE_EXPECTED = "STEPUP_OVERWRITE_EXPECTED" in os.environ


@pytest.mark.parametrize(
    "name",
    [
        "abbreviate-journals",
        "aux-empty",
        "aux-missing",
        "aux-unused",
        "drop-entries",
        "duplicate-doi-ignore",
        "duplicate-doi-fail",
        "duplicate-doi-merge-fail",
        "duplicate-doi-merge-pass",
        "minimal",
        "normalize-doi",
        "normalize-whitespace",
        "pages-range-broken",
        "pages-range1",
        "pages-range2",
        "pages-strip",
        "policy-may",
        "policy-must-fail",
        "policy-must-pass",
        "sort",
        "sort-missing-fields",
        "strip-braces",
    ],
)
def test_bibsane_cases(name):
    args = ["input.bib", "--out", "current.bib"]
    with contextlib.chdir(f"tests/bibsane/{name}"):
        path_config = Path("bibsane.yaml")
        if path_config.exists():
            args += ["--config", str(path_config)]
        path_aux = Path("document.aux")
        if path_aux.exists():
            args += ["--aux", str(path_aux)]

        Path("current.bib").remove_p()
        with open("current.out", "w") as f_out, contextlib.redirect_stdout(f_out):
            bibsane_main(args)

        for suffix in ["bib", "out"]:
            path_expected = Path(f"expected.{suffix}")
            path_current = Path(f"current.{suffix}")
            if OVERWRITE_EXPECTED:
                if path_current.exists():
                    path_current.copy(path_expected)
            elif path_expected.exists():
                assert path_current.exists()
                with open(path_current) as f:
                    current = f.read()
                with open(path_expected) as f:
                    expected = f.read()
                assert current == expected
            else:
                assert not path_current.exists()
