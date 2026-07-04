# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
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
