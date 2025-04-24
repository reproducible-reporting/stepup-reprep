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
        "b25ac67550816e84f2a5689115534c8b1d72081f14f6bc4395e4af41c1dfa831"
        "63d5433ae05e4cba54e04364d38f9084ec9c3e41d0fbe45da3b738939b1aec11"
    )
    assert summary.path == "../sub/a.txt"


BASIC_INVENTORY = """\
              4 -rw-r--r-- b25ac67550816e84f2a5689115534c8b1d72081f14f6bc4395e4af41c1dfa83163d5433a\
e05e4cba54e04364d38f9084ec9c3e41d0fbe45da3b738939b1aec11 a.txt
              4 -rw-r--r-- 10901f8827ee64f82d48afd9fc4a9bf9befaea8cf0b00a4bf16b1533cae88c04f7b467b4\
c59a690462e898e75a0def6c0168b3aef7d01600944f811b4b75da35 b.txt
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
              5 -rw-r--r-- ef15eaf92d5e335345a3e1d977bc7d8797c3d275717cc1b10af79c93cda01aeb2a0c59bc\
02e2bdf9380fd1b54eb9e1669026930ccc24bd49748e65f9a6b2ee68 dest.txt
                lrwxrwxrwx 35d3c7e91999a8d52f496686b07466d03b7e4d85f2c9a85e2b391df1047cb57a6d1c39b8\
4ace64e72267ec116e3376d47fb4512327688eeecb88cf9883e0738a link.txt
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
    with pytest.raises(OSError):
        make_main(["-o", path_tmp / "inventory.txt", path_tmp])


SYMLINK_DIR_INVENTORY = """\
                lrwxrwxrwx a645e8e6808560219f3710f0d46e4ad2cef0b0745a9ee2605ff8446e3edb7bfe600de66d\
d018a886303fceb7be6c614021b7bc706ca03052b39d43899129e20b link
"""


def test_symbolic_link_directory(path_tmp):
    path_sub = path_tmp / "sub"
    path_sub.mkdir()
    with contextlib.chdir(path_tmp):
        Path("link").symlink_to("sub")
        make_main(["-o", "inventory.txt", "link"])
        with open("inventory.txt") as fh:
            assert fh.read() == SYMLINK_DIR_INVENTORY
        check_main(["inventory.txt"])


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
        Path("link").symlink_to("sub")
        make_main(["-o", "inventory2.txt", "sub/dest.txt", "link.txt", "link"])
        check_main(["inventory2.txt"])
        zip_main(["inventory2.txt", "archive.zip"])
        Path("sub/dest.txt").remove()
        Path("sub/").rmdir()
        Path("link.txt").remove()
        Path("link").remove()
        Path("inventory2.txt").move("inventory1.txt")
        os.system("unzip archive.zip")
        check_main(["inventory1.txt"])
        check_main(["inventory2.txt"])
