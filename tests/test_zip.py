# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.zip_inventory."""

import contextlib
import zipfile

from stepup.reprep.make_inventory import write_inventory
from stepup.reprep.zip_inventory import zip_inventory


def test_simple_chdir(path_tmp):
    with contextlib.chdir(path_tmp):
        with open("a.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write("Aaa")
        with open("b.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write("Bbb")
        write_inventory("inventory.jsonl", ["a.txt", "b.txt"])
        zip_inventory("inventory.jsonl", "test.zip")
        with zipfile.ZipFile("test.zip", "r") as fz:
            assert fz.namelist() == ["a.txt", "b.txt"]
            assert fz.read("a.txt") == b"Aaa"
            assert fz.read("b.txt") == b"Bbb"


def test_simple(path_tmp):
    with open(path_tmp / "a.txt", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("Aaa")
    with open(path_tmp / "b.txt", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("Bbb")
    write_inventory(path_tmp / "inventory.jsonl", [path_tmp / "a.txt", path_tmp / "b.txt"])
    zip_inventory(path_tmp / "inventory.jsonl")
    with zipfile.ZipFile(path_tmp / "inventory.zip", "r") as fz:
        assert fz.namelist() == ["a.txt", "b.txt"]
        assert fz.read("a.txt") == b"Aaa"
        assert fz.read("b.txt") == b"Bbb"
