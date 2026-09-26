# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.api."""

import pytest

from stepup.reprep.api import compile_tectonic, convert_jupyter


def test_compile_tectonic_dest_file():
    with pytest.raises(ValueError, match="must be a directory"):
        compile_tectonic("paper.tex", "other.pdf")


@pytest.fixture
def run_commands(monkeypatch) -> list[str]:
    """Replace `run()` in the API module by a function that records the commands."""
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)

    monkeypatch.setattr("stepup.reprep.api.run", fake_run)
    return commands


def test_convert_jupyter_timeout(run_commands: list[str]):
    convert_jupyter("demo.ipynb", timeout=1200)
    assert run_commands == [
        "srr-convert-jupyter demo.ipynb demo.html --to html --execute --timeout=1200"
    ]


def test_convert_jupyter_timeout_zero(run_commands: list[str]):
    convert_jupyter("demo.ipynb", timeout=0)
    assert run_commands == [
        "srr-convert-jupyter demo.ipynb demo.html --to html --execute --timeout=0"
    ]


def test_convert_jupyter_timeout_default(run_commands: list[str]):
    convert_jupyter("demo.ipynb")
    assert run_commands == ["srr-convert-jupyter demo.ipynb demo.html --to html --execute"]


def test_convert_jupyter_timeout_no_execute(run_commands: list[str]):
    convert_jupyter("demo.ipynb", execute=False, timeout=1200)
    assert run_commands == ["srr-convert-jupyter demo.ipynb demo.html --to html"]


@pytest.mark.parametrize("timeout", [-1, 1.5, "60", True])
def test_convert_jupyter_timeout_invalid(run_commands: list[str], timeout):
    with pytest.raises(ValueError, match="timeout must be a non-negative integer"):
        convert_jupyter("demo.ipynb", timeout=timeout)
    assert run_commands == []
