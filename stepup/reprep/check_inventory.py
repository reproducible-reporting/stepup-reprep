# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Checking of inventory files."""

import argparse
import sys
from collections.abc import Sequence

from stepup.core.path import Path, StrPath

from .inventory import check_record, compute_record, open_inventory

__all__ = ("check_inventory", "main")


def main(argv: Sequence[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="srr-check-inventory", description="Check the files listed in an inventory."
    )
    parser.add_argument(
        "inventory", help="An inventory file with suffix .jsonl, written by srr-make-inventory."
    )
    args = parser.parse_args(argv)
    if not args.inventory.endswith(".jsonl"):
        raise ValueError("The inventory file must end with .jsonl")
    check_inventory(args.inventory)


def check_inventory(path_inventory: StrPath):
    """Check that the files on disk match the records of an inventory.

    Parameters
    ----------
    path_inventory
        The inventory file.
        The paths of its records are relative to its parent directory.

    Raises
    ------
    ValueError
        When the inventory cannot be read or when a file differs from its record.
    """
    path_inventory = Path(path_inventory)
    root = path_inventory.parent
    with open_inventory(path_inventory) as reader:
        header = reader.header
        for ref in reader:
            new = compute_record(root / ref.path, root, header.hash_algorithm, header.mode)
            check_record(new, ref)


if __name__ == "__main__":
    sys.exit(main())
