# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.sync_zenodo."""

import pytest

from stepup.reprep.sync_zenodo import Creator


@pytest.mark.parametrize(
    "orcid",
    ["0000-0001-9288-5608", "0000-0001-6785-333X", "0000-0001-6785-333x", "0000-0002-0257-4687"],
)
def test_creator_orcid_valid(orcid):
    Creator("Test User", "StepUp RepRep", {"orcid": orcid})


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
        Creator("Test User", "StepUp RepRep", {"orcid": orcid})
