# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# Copyright 2024-2026 Toon Verstraelen
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
"""Unit tests for stepup.reprep.bibparser"""

import json
import os

import pytest

from stepup.reprep.bibparser import BibtexParseError, format_bib, parse_bib

OVERWRITE_EXPECTED = "STEPUP_OVERWRITE_EXPECTED" in os.environ


@pytest.mark.parametrize(
    "name",
    [
        "mixed",
        "realistic",
        "external",
    ],
)
def test_correct(name: str) -> None:
    """Test bibparser on an example."""
    with open(f"tests/bibparser/correct/{name}.bib") as fp:
        entries = parse_bib(fp.read())

    # Compare against expected output
    if OVERWRITE_EXPECTED:
        with open(f"tests/bibparser/correct/{name}.json", "w") as fp:
            json.dump(entries, fp, indent=2)
            fp.write("\n")
    else:
        with open(f"tests/bibparser/correct/{name}.json") as fp:
            expected = json.load(fp)
        assert entries == expected

    # Consistency check: re-format and parse again
    formatted = format_bib(entries)
    entries2 = parse_bib(formatted)
    assert entries == entries2


@pytest.mark.parametrize(
    "name",
    [
        "comment",
        "identifier_without_comma",
        "missing_comma",
        "preamble",
        "string",
        "unclosed1",
        "unclosed2",
    ],
)
def test_wrong(name: str) -> None:
    """Test bibparser on an example that should raise an error."""
    with open(f"tests/bibparser/wrong/{name}.bib") as fp:
        text = fp.read()
    with pytest.raises(BibtexParseError):
        parse_bib(text)
