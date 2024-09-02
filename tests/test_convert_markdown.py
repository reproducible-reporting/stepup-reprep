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
"""Unit tests for stepup.reprep.convert_markdown."""

import pytest

from stepup.reprep.convert_markdown import isolate_header

KATEX = r"""
<ul>
<li>
[1/1]
<math xmlns="http://www.w3.org/1998/Math/MathML">
<semantics>
<mrow><mi>x</mi><mo>=</mo><mfrac>
<mrow><mi>a</mi><msup><mi>t</mi><mn>2</mn></msup></mrow>
<mn>2</mn></mfrac></mrow>
<annotation encoding="application/x-tex">x=\frac{at^2}{2}</annotation>
</semantics>
</math>
</li>
</ul>
""".replace("\n", "")


SPAN_EXAMPLE = '<span style="height:2.476em;vertical-align:-0.9119em;"></span>'


@pytest.mark.parametrize(
    ("orig_body", "header", "body"),
    [
        ("<p>first</p><title>foo</title>", "<title>foo</title>", "<p>first</p>"),
        ("<p>first</p><p>second</p>", "", "<p>first</p><p>second</p>"),
        (
            '<title>foo</title><link rel="stylesheet" href="foo.css" />',
            '<title>foo</title><link href="foo.css" rel="stylesheet"/>',
            "",
        ),
        (KATEX, "", KATEX),
        (SPAN_EXAMPLE, "", SPAN_EXAMPLE),
    ],
)
def test_isolate_header(orig_body, header, body):
    assert isolate_header(orig_body) == (header, body)
    # assert False
