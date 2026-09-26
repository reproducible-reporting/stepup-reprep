# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.convert_jupyter."""

import pytest
from nbformat import v4

from stepup.reprep.convert_jupyter import (
    NO_TIMEOUT_TAG,
    get_cell_timeout,
    parse_args,
    resolve_timeout,
)


def test_resolve_timeout_unset(monkeypatch):
    monkeypatch.delenv("REPREP_JUPYTER_TIMEOUT", raising=False)
    assert resolve_timeout(None) is None


def test_resolve_timeout_empty_variable(monkeypatch):
    monkeypatch.setenv("REPREP_JUPYTER_TIMEOUT", "")
    assert resolve_timeout(None) is None


def test_resolve_timeout_variable(monkeypatch):
    monkeypatch.setenv("REPREP_JUPYTER_TIMEOUT", "300")
    assert resolve_timeout(None) == 300


def test_resolve_timeout_variable_zero(monkeypatch):
    monkeypatch.setenv("REPREP_JUPYTER_TIMEOUT", "0")
    assert resolve_timeout(None) is None


def test_resolve_timeout_argument(monkeypatch):
    monkeypatch.delenv("REPREP_JUPYTER_TIMEOUT", raising=False)
    assert resolve_timeout(120) == 120


def test_resolve_timeout_argument_overrides_variable(monkeypatch):
    monkeypatch.setenv("REPREP_JUPYTER_TIMEOUT", "300")
    assert resolve_timeout(120) == 120
    assert resolve_timeout(0) is None


@pytest.mark.parametrize("value", ["abc", "-5", "1.5"])
def test_resolve_timeout_invalid_variable(monkeypatch, value: str):
    monkeypatch.setenv("REPREP_JUPYTER_TIMEOUT", value)
    with pytest.raises(ValueError, match="REPREP_JUPYTER_TIMEOUT"):
        resolve_timeout(None)


def test_resolve_timeout_invalid_argument(monkeypatch):
    monkeypatch.delenv("REPREP_JUPYTER_TIMEOUT", raising=False)
    with pytest.raises(ValueError, match="The timeout must be a non-negative integer"):
        resolve_timeout(-5)


def test_get_cell_timeout_untagged():
    cell = v4.new_code_cell("pass")
    assert get_cell_timeout(cell, 60) == 60


def test_get_cell_timeout_tagged():
    cell = v4.new_code_cell("pass", metadata={"tags": [NO_TIMEOUT_TAG]})
    assert get_cell_timeout(cell, 60) is None


def test_get_cell_timeout_other_tags():
    cell = v4.new_code_cell("pass", metadata={"tags": ["parameters"]})
    assert get_cell_timeout(cell, 60) == 60


def test_parse_args_timeout():
    assert parse_args(["demo.ipynb", "demo.html"]).timeout is None
    assert parse_args(["demo.ipynb", "demo.html", "--timeout=30"]).timeout == 30
