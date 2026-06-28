# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# Copyright 2024-2026 Toon Verstraelen
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
"""Unit tests for inventory files."""

import contextlib
import os

import pytest
from path import Path

from stepup.reprep.check_inventory import main as check_main
from stepup.reprep.inventory import get_summary
from stepup.reprep.make_inventory import main as make_main
from stepup.reprep.make_inventory import parse_inventory_def
from stepup.reprep.zip_inventory import main as zip_main


def test_get_summary(path_tmp):
    (path_tmp / "sub").mkdir()
    with open(path_tmp / "sub/a.txt", "w") as fh:
        print("aaa", file=fh)
    summary = get_summary(path_tmp / "sub/a.txt", path_tmp / "other")
    assert summary.size == 4
    assert summary.mode == "-rw-r--r--"
    assert summary.digest.hex() == (
        "17e682f060b5f8e47ea04c5c4855908b0a5ad612022260fe50e11ecb0cc0ab76"
    )
    assert summary.path == "../sub/a.txt"


BASIC_INVENTORY = """\
              4 -rw-r--r-- 17e682f060b5f8e47ea04c5c4855908b0a5ad612022260fe50e11ecb0cc0ab76 a.txt
              4 -rw-r--r-- 3cf9a1a81f6bdeaf08a343c1e1c73e89cf44c06ac2427a892382cae825e7c9c1 b.txt
"""


def test_basic(path_tmp):
    with contextlib.chdir(path_tmp):
        with open("a.txt", "w") as fh:
            print("aaa", file=fh)
        with open("b.txt", "w") as fh:
            print("bbb", file=fh)
        with open("inventory.def", "w") as fh:
            print("include *.txt", file=fh)
        make_main(["-i", "inventory.def"])
        with open("inventory.txt") as fh:
            assert fh.read() == BASIC_INVENTORY
        make_main(["-o", "inventory2.txt", "a.txt", "b.txt"])
        with open("inventory2.txt") as fh:
            assert fh.read() == BASIC_INVENTORY
        check_main(["inventory.txt"])


SYMLINK_INVENTORY = """\
              5 -rw-r--r-- 185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969 dest.txt
                lrwxrwxrwx ead30c9e7e28b7aa64ae7bbfe4c4d8fc873387b77b86da5f09e06cbdc3166d22 link.txt
"""


def test_symbolic_link(path_tmp):
    with contextlib.chdir(path_tmp):
        with open("dest.txt", "w") as fh:
            fh.write("Hello")
        Path("link.txt").symlink_to("dest.txt")
        make_main(["-o", "inventory.txt", "dest.txt", "link.txt"])
        with open("inventory.txt") as fh:
            assert fh.read() == SYMLINK_INVENTORY
        check_main(["inventory.txt"])


def test_directory(path_tmp):
    with pytest.raises(ValueError):
        make_main(["-o", path_tmp / "inventory.txt", path_tmp])


def test_symbolic_link_directory(path_tmp):
    path_sub = path_tmp / "sub"
    path_sub.mkdir()
    with contextlib.chdir(path_tmp):
        Path("link").symlink_to("sub")
        with pytest.raises(ValueError):
            make_main(["-o", "inventory.txt", "link"])


def test_git1():
    with contextlib.chdir("tests/examples/check_hrefs_md"):
        paths = parse_inventory_def(["include-git\n"])
    assert paths == {
        "main.sh",
        "expected_graph.txt",
        "plan.py",
        "test.md",
        "expected_stdout.txt",
        "README.txt",
        "check_hrefs.yaml",
        ".gitignore",
    }


def test_git2():
    paths = parse_inventory_def(["include-git tests/examples/check_hrefs_md\n"])
    assert paths == {
        "tests/examples/check_hrefs_md/" + path
        for path in [
            "main.sh",
            "expected_graph.txt",
            "plan.py",
            "test.md",
            "expected_stdout.txt",
            "README.txt",
            "check_hrefs.yaml",
            ".gitignore",
        ]
    }


def test_zip_inventory(path_tmp):
    with contextlib.chdir(path_tmp):
        Path("sub").mkdir()
        with open("sub/dest.txt", "w") as fh:
            fh.write("Hello")
        Path("link.txt").symlink_to("sub/dest.txt")
        make_main(["-o", "inventory2.txt", "sub/dest.txt", "link.txt"])
        check_main(["inventory2.txt"])
        zip_main(["inventory2.txt", "archive.zip"])
        Path("sub/dest.txt").remove()
        Path("sub/").rmdir()
        Path("link.txt").remove()
        Path("inventory2.txt").move("inventory1.txt")
        os.system("unzip archive.zip")
        check_main(["inventory1.txt"])
        check_main(["inventory2.txt"])
