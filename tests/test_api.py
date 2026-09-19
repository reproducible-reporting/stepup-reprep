# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.api."""

import pytest

from stepup.reprep.api import compile_tectonic


def test_compile_tectonic_dest_file():
    with pytest.raises(ValueError, match="must be a directory"):
        compile_tectonic("paper.tex", "other.pdf")
