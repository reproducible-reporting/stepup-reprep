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
"""Utilities for testing with pytest."""

from path import Path

from stepup.core.pytest import run_example as run_example_core
from stepup.reprep.check_manifest import iter_manifest

__all__ = ("run_example",)


async def run_example(srcdir, tmpdir, overwrite_expected=False):
    """Run an example use case in a temporary directory and check the outputs.

    See stepup.core.pytest.run_example for details.
    """
    await run_example_core(srcdir, tmpdir, overwrite_expected)

    # Reproducibility check
    workdir = Path(tmpdir) / "example"
    for path_manifest in sorted(workdir.glob("reproducibility_*manifest.txt")):
        records = list(iter_manifest(path_manifest))
        sizes = {record[0] for record in records}
        if not len(sizes) == 1:
            raise AssertionError(f"Not all file sizes in {path_manifest} are the same.")
        digests = {record[1] for record in records}
        if not len(digests) == 1:
            raise AssertionError(f"Not all file digests in {path_manifest} are the same.")
