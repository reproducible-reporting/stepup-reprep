# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Pytest configuration."""

import subprocess

import pytest
from path import Path

pytest.register_assert_rewrite("stepup.core.pytest", "stepup.reprep.pytest")


@pytest.fixture
def path_tmp(tmpdir: str) -> Path:
    return Path(tmpdir)


def run_tool(*args: str):
    """Run one of the RepRep command-line tools in a subprocess, as StepUp does."""
    subprocess.run(args, stdin=subprocess.DEVNULL, check=True)
