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
"""Unit tests for stepup.reprep.sync_zenodo."""

import pytest

from stepup.reprep.sync_zenodo import Creator, ZenodoWrapper


def test_links():
    zenodo = ZenodoWrapper("")
    links = {"foo": f"{zenodo.endpoint}/foo"}
    zenodo._normalize_links(links)
    assert links == {"foo": "foo"}


@pytest.mark.parametrize(
    "orcid",
    ["0000-0001-9288-5608", "0000-0001-6785-333X", "0000-0001-6785-333x", "0000-0002-0257-4687"],
)
def test_creator_orcid_valid(orcid):
    Creator("Test User", "StepUp RepRep", orcid)


@pytest.mark.parametrize(
    "orcid",
    [
        "0000-0002-0257-4687  0000-0002-0257-46870000-0001-9288-560x",
        "0000-0001-9288-560X",
        "0000-0001-6785-3337",
        "0000-0002-1825-009",
        "0000-0002-1825-00977",
        "000-0002-1825-0097",
        "0000X0002-1825-0097",
        "https://orcid.org/0000-0002-1825-0097",
        "ABCD-EFGH-IJKL-MNOP",
        "1234-5678-9012-345y",
        "",
        "    ",
        "0000-0002-1825-0090",
        "0000-0002-1694-233A",
    ],
)
def test_creator_orcid_invalid(orcid):
    with pytest.raises(ValueError):
        Creator("Test User", "StepUp RepRep", orcid)
