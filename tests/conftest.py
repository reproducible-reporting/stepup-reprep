# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Pytest configuration."""

import pytest
from path import Path

pytest.register_assert_rewrite("stepup.core.pytest", "stepup.reprep.pytest")


@pytest.fixture
def path_tmp(tmpdir: str) -> Path:
    return Path(tmpdir)
