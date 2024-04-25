# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# Copyright (C) 2024 Toon Verstraelen
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
"""Unit tests for stepup.reprep.zip_manifest."""

import contextlib
import zipfile

from stepup.reprep.make_manifest import write_manifest
from stepup.reprep.zip_manifest import zip_manifest


def test_simple_chdir(path_tmp):
    with contextlib.chdir(path_tmp):
        with open("a.txt", "w") as fh:
            fh.write("Aaa")
        with open("b.txt", "w") as fh:
            fh.write("Bbb")
        write_manifest("MANIFEST.txt", ["a.txt", "b.txt"])
        zip_manifest("MANIFEST.txt", "test.zip")
        contents = {}
        with zipfile.ZipFile("test.zip", "r") as fz:
            for name in fz.namelist():
                contents[name] = fz.read(name).decode("utf-8")
        assert contents["a.txt"] == "Aaa"
        assert contents["b.txt"] == "Bbb"
        assert "MANIFEST.txt" in contents


def test_simple(path_tmp):
    with open(path_tmp / "a.txt", "w") as fh:
        fh.write("Aaa")
    with open(path_tmp / "b.txt", "w") as fh:
        fh.write("Bbb")
    write_manifest(path_tmp / "MANIFEST.txt", [path_tmp / "a.txt", path_tmp / "b.txt"])
    zip_manifest(path_tmp / "MANIFEST.txt", path_tmp / "test.zip")
    contents = {}
    with zipfile.ZipFile(path_tmp / "test.zip", "r") as fz:
        for name in fz.namelist():
            contents[name] = fz.read(name).decode("utf-8")
    assert contents["a.txt"] == "Aaa"
    assert contents["b.txt"] == "Bbb"
    assert "MANIFEST.txt" in contents
