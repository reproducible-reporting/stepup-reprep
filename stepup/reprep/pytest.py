# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
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
