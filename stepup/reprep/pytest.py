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
"""Utilities for testing with pytest."""

from path import Path

from stepup.core.pytest import run_example as run_example_core
from stepup.reprep.check_inventory import iter_inventory

__all__ = ("run_example",)


async def run_example(srcdir, tmpdir, overwrite_expected=False):
    """Run an example use case in a temporary directory and check the outputs.

    See stepup.core.pytest.run_example for details.
    """
    await run_example_core(srcdir, tmpdir, overwrite_expected=overwrite_expected)

    # Reproducibility check
    workdir = Path(tmpdir) / "example"
    for path_inventory in sorted(workdir.glob("reproducibility_*inventory.txt")):
        records = list(iter_inventory(path_inventory))
        sizes = {record.size for record in records}
        if len(sizes) != 1:
            raise AssertionError(f"Not all file sizes in {path_inventory} are the same.")
        digests = {record.digest for record in records}
        if len(digests) != 1:
            raise AssertionError(f"Not all file digests in {path_inventory} are the same.")
