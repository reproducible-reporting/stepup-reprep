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
"""Unit tests for manifest files."""

import contextlib

from stepup.reprep.check_manifest import main as check_main
from stepup.reprep.make_manifest import main as make_main

BASIC_MANIFEST = """\
              4 b25ac67550816e84f2a5689115534c8b1d72081f14f6bc4395e4af41c1dfa83163d5433ae05e4cba54e\
04364d38f9084ec9c3e41d0fbe45da3b738939b1aec11 a.txt
              4 10901f8827ee64f82d48afd9fc4a9bf9befaea8cf0b00a4bf16b1533cae88c04f7b467b4c59a690462e\
898e75a0def6c0168b3aef7d01600944f811b4b75da35 b.txt
"""


def test_basic(tmpdir):
    with contextlib.chdir(tmpdir):
        with open("a.txt", "w") as fh:
            print("aaa", file=fh)
        with open("b.txt", "w") as fh:
            print("bbb", file=fh)
        with open("MANIFEST.in", "w") as fh:
            print("include *.txt", file=fh)
        make_main(["-i", "MANIFEST.in"])
        with open("MANIFEST.txt") as fh:
            assert fh.read() == BASIC_MANIFEST
        make_main(["-o", "MANIFEST2.txt", "a.txt", "b.txt"])
        with open("MANIFEST2.txt") as fh:
            assert fh.read() == BASIC_MANIFEST
        check_main(["MANIFEST.txt"])
