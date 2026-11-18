# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Utilities for testing with pytest."""

import re
from collections.abc import Sequence

from stepup.core.path import Path
from stepup.core.platform.oscompat import file_modes_available
from stepup.core.pytest import OUTPUT_RULES as CORE_OUTPUT_RULES
from stepup.core.pytest import OutputRule
from stepup.core.pytest import run_example as run_example_core
from stepup.reprep.check_inventory import iter_inventory

__all__ = ("INVENTORY_OUTPUT", "OUTPUT_RULES", "run_example")


INVENTORY_MODE = re.compile(r"^(.{16}.).{9}", re.MULTILINE)
"""The permission bits of the file mode on a line of an inventory.

The group holds what precedes them, up to and including the file type.
"""


def mask_inventory_modes(text: str) -> str:
    """Hide the permission bits of the file modes in the lines of an inventory.

    The first character of each mode, which gives the type of the file, is kept.
    `mask_file_modes` in `stepup.core.pytest` does the same for the output of StepUp.
    """
    return INVENTORY_MODE.sub(r"\1*********", text)


def mask_inventory_output(text: str) -> str:
    """Hide the parts of an inventory that may differ in this environment.

    On a platform without permission bits of files,
    the file modes are hidden, see `mask_inventory_modes`.
    """
    return text if file_modes_available() else mask_inventory_modes(text)


INVENTORY_OUTPUT = OutputRule("_*inventory.txt", mask=mask_inventory_output)
"""The rule for an inventory file, as written by `make_inventory()`."""

OUTPUT_RULES = (INVENTORY_OUTPUT, *CORE_OUTPUT_RULES)
"""The rules that `run_example` applies by default, those of StepUp Core included."""


async def run_example(
    srcdir: Path,
    tmpdir: Path,
    overwrite_expected: bool = False,
    *,
    rules: Sequence[OutputRule] = OUTPUT_RULES,
):
    """Run an example use case in a temporary directory and check the outputs.

    See `stepup.core.pytest.run_example` for details and for the parameters.
    After the comparison, all files listed in an inventory `reproducibility_*inventory.txt`
    in the example must have the same size and digest.
    """
    await run_example_core(Path(srcdir), Path(tmpdir), overwrite_expected, rules=rules)

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
