# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for inventory files."""

import contextlib
import hashlib
import os
import stat
import tempfile
import zipfile

import pytest

from stepup.core.path import Path
from stepup.core.platform.oscompat import file_modes_available
from stepup.reprep.check_inventory import main as check_main
from stepup.reprep.inventory import FileSummary, check_summary, get_summary
from stepup.reprep.make_inventory import main as make_main
from stepup.reprep.make_inventory import parse_inventory_def
from stepup.reprep.pytest import mask_inventory_modes
from stepup.reprep.zip_inventory import main as zip_main


def symlinks_available() -> bool:
    """Whether this user can create symbolic links, which takes a privilege on Windows."""
    with tempfile.TemporaryDirectory() as path:
        try:
            os.symlink("target", Path(path) / "link")
        except (OSError, NotImplementedError):
            return False
    return True


needs_symlinks = pytest.mark.skipif(not symlinks_available(), reason="Cannot create symbolic links")


def assert_inventory(path: str, expected: str):
    """Compare an inventory file with the expected one, without file modes where files have none."""
    with open(path, encoding="utf-8") as fh:
        current = fh.read()
    if not file_modes_available():
        current = mask_inventory_modes(current)
        expected = mask_inventory_modes(expected)
    assert current == expected


def test_get_summary(path_tmp):
    (path_tmp / "sub").mkdir()
    with open(path_tmp / "sub/a.txt", "w", encoding="utf-8", newline="\n") as fh:
        print("aaa", file=fh)
    summary = get_summary(path_tmp / "sub/a.txt", path_tmp / "other")
    assert summary.size == 4
    if file_modes_available():
        assert summary.mode == "-rw-r--r--"
    else:
        assert summary.mode.startswith("-")
    assert summary.digest.hex() == (
        "17e682f060b5f8e47ea04c5c4855908b0a5ad612022260fe50e11ecb0cc0ab76"
    )
    assert summary.path == "../sub/a.txt"


@pytest.mark.parametrize("modes", [True, False])
def test_check_summary_modes(monkeypatch, modes: bool):
    monkeypatch.setattr("stepup.reprep.inventory.file_modes_available", lambda: modes)
    ref = FileSummary(4, "-rw-r--r--", bytes(32), "a.txt")
    other_mode = FileSummary(4, "-rw-rw-rw-", bytes(32), "a.txt")
    if modes:
        with pytest.raises(ValueError, match="File mode"):
            check_summary(other_mode, ref)
    else:
        check_summary(other_mode, ref)
    with pytest.raises(ValueError, match="File size"):
        check_summary(FileSummary(5, "-rw-r--r--", bytes(32), "a.txt"), ref)
    with pytest.raises(ValueError, match="File digest"):
        check_summary(FileSummary(4, "-rw-r--r--", bytes([1] * 32), "a.txt"), ref)


BASIC_INVENTORY = """\
              4 -rw-r--r-- 17e682f060b5f8e47ea04c5c4855908b0a5ad612022260fe50e11ecb0cc0ab76 a.txt
              4 -rw-r--r-- 3cf9a1a81f6bdeaf08a343c1e1c73e89cf44c06ac2427a892382cae825e7c9c1 b.txt
"""


def test_basic(path_tmp):
    with contextlib.chdir(path_tmp):
        with open("a.txt", "w", encoding="utf-8", newline="\n") as fh:
            print("aaa", file=fh)
        with open("b.txt", "w", encoding="utf-8", newline="\n") as fh:
            print("bbb", file=fh)
        with open("inventory.def", "w", encoding="utf-8", newline="\n") as fh:
            print("include *.txt", file=fh)
        make_main(["-i", "inventory.def"])
        assert_inventory("inventory.txt", BASIC_INVENTORY)
        make_main(["-o", "inventory2.txt", "a.txt", "b.txt"])
        assert_inventory("inventory2.txt", BASIC_INVENTORY)
        check_main(["inventory.txt"])


SYMLINK_INVENTORY = """\
              5 -rw-r--r-- 185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969 dest.txt
                lrwxrwxrwx ead30c9e7e28b7aa64ae7bbfe4c4d8fc873387b77b86da5f09e06cbdc3166d22 link.txt
"""


@needs_symlinks
def test_symbolic_link(path_tmp):
    with contextlib.chdir(path_tmp):
        with open("dest.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write("Hello")
        Path("link.txt").symlink_to("dest.txt")
        make_main(["-o", "inventory.txt", "dest.txt", "link.txt"])
        assert_inventory("inventory.txt", SYMLINK_INVENTORY)
        check_main(["inventory.txt"])


def test_directory(path_tmp):
    with pytest.raises(ValueError):
        make_main(["-o", path_tmp / "inventory.txt", path_tmp])


@needs_symlinks
def test_symbolic_link_directory(path_tmp):
    path_sub = path_tmp / "sub"
    path_sub.mkdir()
    with contextlib.chdir(path_tmp):
        Path("link").symlink_to("sub", target_is_directory=True)
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


def extract_zip(path_zip: str):
    """Extract a ZIP file in the current directory, with its file modes and symbolic links.

    `ZipFile.extract` writes a symbolic link as a file that contains the target,
    see [cpython#82102](https://github.com/python/cpython/issues/82102).
    The target of a link is stored with `/` separators,
    and Windows does not resolve a link whose target is written in that way,
    as observed on Windows 11.
    """
    with zipfile.ZipFile(path_zip) as fz:
        for info in fz.infolist():
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                os.symlink(os.path.normpath(fz.read(info).decode("utf-8")), info.filename)
            else:
                fz.extract(info)
                os.chmod(info.filename, stat.S_IMODE(mode))


@needs_symlinks
def test_zip_inventory(path_tmp):
    with contextlib.chdir(path_tmp):
        Path("sub").mkdir()
        with open("sub/dest.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write("Hello")
        Path("link.txt").symlink_to(os.path.normpath("sub/dest.txt"))
        make_main(["-o", "inventory2.txt", "sub/dest.txt", "link.txt"])
        # The target of a link is hashed and archived with `/`, also on Windows.
        assert get_summary("link.txt", ".").digest == hashlib.sha256(b"sub/dest.txt").digest()
        check_main(["inventory2.txt"])
        zip_main(["inventory2.txt", "archive.zip"])
        with zipfile.ZipFile("archive.zip") as fz:
            assert fz.read("link.txt") == b"sub/dest.txt"
        Path("sub/dest.txt").remove()
        Path("sub/").rmdir()
        Path("link.txt").remove()
        Path("inventory2.txt").move("inventory1.txt")
        extract_zip("archive.zip")
        check_main(["inventory1.txt"])
        check_main(["inventory2.txt"])
