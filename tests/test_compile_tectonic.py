# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.compile_tectonic"""

import pytest

from stepup.reprep.compile_tectonic import parse_makefile_rules


@pytest.mark.parametrize(
    ("text", "out_paths", "inp_paths"),
    [
        (
            "paper.pdf : paper.tex \\\n  generated.tex \\\n  smile.pdf\n",
            ["paper.pdf"],
            ["paper.tex", "generated.tex", "smile.pdf"],
        ),
        ("../out\\paper.pdf : paper.tex\n", ["../out\\paper.pdf"], ["paper.tex"]),
        (
            "C:\\work\\out\\paper.pdf : paper.tex \\\n  C:\\work\\out\\smile.pdf\n",
            ["C:\\work\\out\\paper.pdf"],
            ["paper.tex", "C:\\work\\out\\smile.pdf"],
        ),
        (": paper.tex\n", [], ["paper.tex"]),
    ],
)
def test_parse_makefile_rules(text: str, out_paths: list[str], inp_paths: list[str]):
    assert parse_makefile_rules(text) == (out_paths, inp_paths)
