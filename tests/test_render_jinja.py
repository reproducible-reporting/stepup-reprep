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
"""Unit tests for stepup.reprep.render."""

from stepup.reprep.render_jinja import load_module_file


def test_load_module_file(path_tmp):
    path_foo = path_tmp / "foo.py"
    with open(path_foo, "w") as fh:
        print("a = 10", file=fh)
    foo = load_module_file(path_foo)
    assert foo.a == 10


def test_load_module_file2(path_tmp):
    path_foo = path_tmp / "foo.py"
    with open(path_foo, "w") as fh:
        print("a = 10", file=fh)
    path_bar = path_tmp / "bar.py"
    with open(path_bar, "w") as fh:
        print("from foo import a", file=fh)
    bar = load_module_file(path_bar)
    assert bar.a == 10
