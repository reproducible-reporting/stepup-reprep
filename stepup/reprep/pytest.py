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
from stepup.reprep.inventory import FileRecord, open_inventory

__all__ = ("INVENTORY_OUTPUT", "OUTPUT_RULES", "run_example")


INVENTORY_MODE = re.compile(r'"mode":"[^"]{9}"')
"""The permission bits of a file in a record of an inventory."""


def mask_inventory_modes(text: str) -> str:
    """Hide the permission bits of the files in the records of an inventory.

    `mask_file_modes` in `stepup.core.pytest` does the same for the output of StepUp.
    """
    return INVENTORY_MODE.sub('"mode":"*********"', text)


def mask_inventory_output(text: str) -> str:
    """Hide the parts of an inventory that may differ in this environment.

    On a platform without permission bits of files,
    the permission bits are hidden, see `mask_inventory_modes`.
    """
    return text if file_modes_available() else mask_inventory_modes(text)


INVENTORY_OUTPUT = OutputRule("_*inventory.jsonl", mask=mask_inventory_output)
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
    After the comparison, all regular files listed in an inventory
    `reproducibility_*inventory.jsonl` in the example must have the same size and digest.
    """
    await run_example_core(Path(srcdir), Path(tmpdir), overwrite_expected, rules=rules)

    # Reproducibility check
    workdir = Path(tmpdir) / "example"
    for path_inventory in sorted(workdir.glob("reproducibility_*inventory.jsonl")):
        with open_inventory(path_inventory) as reader:
            records = [record for record in reader if isinstance(record, FileRecord)]
        sizes = {record.size for record in records}
        if len(sizes) != 1:
            raise AssertionError(f"Not all file sizes in {path_inventory} are the same.")
        digests = {record.digest for record in records}
        if len(digests) != 1:
            raise AssertionError(f"Not all file digests in {path_inventory} are the same.")
