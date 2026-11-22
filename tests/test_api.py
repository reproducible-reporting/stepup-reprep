# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.api."""

import pytest

from stepup.reprep.api import (
    compile_latex,
    compile_tectonic,
    convert_jupyter,
    make_inventory,
    sync_zenodo,
)


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


@pytest.fixture
def run_calls(monkeypatch) -> list[tuple[str, dict]]:
    """Replace `run()` in the API module by a function that records the commands and arguments."""
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return command

    monkeypatch.setattr("stepup.reprep.api.run", fake_run)
    return calls


def test_sync_zenodo(run_calls: list[tuple[str, dict]]):
    """The sync step runs at every start and trusts the inventory built in the workflow."""
    result = sync_zenodo(
        "sync_zenodo.yaml",
        "zenodo_description.md",
        "zenodo_inventory.jsonl",
        resources={"zenodo": 1},
        duration=60.0,
    )
    assert run_calls == [
        (
            "srr-sync-zenodo sync_zenodo.yaml zenodo_description.md zenodo_inventory.jsonl "
            "--no-check-md5",
            {
                "inp": ["sync_zenodo.yaml", "zenodo_description.md", "zenodo_inventory.jsonl"],
                "recheck": True,
                "resources": {"zenodo": 1},
                "duration": 60.0,
            },
        ),
    ]
    assert result == run_calls[0][0]


def test_sync_zenodo_minimal(run_calls: list[tuple[str, dict]]):
    sync_zenodo("sub/other.toml", "sub/other.html", "sub/files.jsonl")
    assert run_calls == [
        (
            "srr-sync-zenodo sub/other.toml sub/other.html sub/files.jsonl --no-check-md5",
            {
                "inp": ["sub/other.toml", "sub/other.html", "sub/files.jsonl"],
                "recheck": True,
                "resources": None,
                "duration": None,
            },
        ),
    ]


def test_sync_zenodo_check_md5(run_calls: list[tuple[str, dict]]):
    sync_zenodo(
        "sync_zenodo.yaml",
        "zenodo_description.md",
        "zenodo_inventory.jsonl",
        check_md5=True,
        verbose=True,
    )
    assert [command for command, _ in run_calls] == [
        "srr-sync-zenodo sync_zenodo.yaml zenodo_description.md zenodo_inventory.jsonl --verbose",
    ]


def test_sync_zenodo_inventory_required(run_calls: list[tuple[str, dict]]):
    with pytest.raises(TypeError):
        sync_zenodo("sync_zenodo.yaml", "zenodo_description.md")
    assert run_calls == []


def test_make_inventory(run_calls: list[tuple[str, dict]]):
    """The explicit paths keep their order, and the defaults add no options."""
    make_inventory("b.txt", "a.txt", "inventory.jsonl", path_def="inventory.def")
    assert run_calls == [
        (
            "srr-make-inventory b.txt a.txt -i inventory.def -o inventory.jsonl",
            {
                "inp": ["b.txt", "a.txt", "inventory.def"],
                "out": ["inventory.jsonl"],
                "optional": False,
                "resources": None,
                "duration": None,
            },
        ),
    ]


def test_make_inventory_options(run_calls: list[tuple[str, dict]]):
    make_inventory("a.txt", "inventory.jsonl", hash_algorithm="sha256", mode=True)
    assert [command for command, _ in run_calls] == [
        "srr-make-inventory a.txt -o inventory.jsonl --hash sha256 --mode",
    ]


def test_make_inventory_no_paths(run_calls: list[tuple[str, dict]]):
    with pytest.raises(ValueError, match="At least one path"):
        make_inventory()
    assert run_calls == []


def test_compile_latex_inventory_default(run_calls: list[tuple[str, dict]]):
    compile_latex("paper.tex", inventory=True)
    command, kwargs = run_calls[0]
    assert "--inventory=paper-inventory.jsonl" in command
    assert "paper-inventory.jsonl" in kwargs["out"]
