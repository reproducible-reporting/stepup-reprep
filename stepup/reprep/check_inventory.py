# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Checking of inventory files."""

import argparse
from collections.abc import Iterator

from path import Path

from .inventory import FileSummary, check_summary, get_summary, parse_summary

__all__ = ("check_inventory", "iter_inventory", "main")


def main(argv: list[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="srr-check-inventory", description="Check an inventory.txt."
    )
    parser.add_argument("inventory_txt", help="An inventory.txt file generated with RepRep")
    args = parser.parse_args(argv)
    if not args.inventory_txt.endswith(".txt"):
        raise ValueError("The inventory file must end with .txt")
    check_inventory(args.inventory_txt)


def iter_inventory(path_inventory: str) -> Iterator[FileSummary]:
    with open(path_inventory) as fh:
        for iline, line in enumerate(fh):
            try:
                fs = parse_summary(line)
            except Exception as exc:
                raise ValueError(f"Could not parse line {iline} of {path_inventory}") from exc
            yield fs


def check_inventory(path_inventory: str):
    path_inventory = Path(path_inventory)
    root = path_inventory.parent
    for ref in iter_inventory(path_inventory):
        new = get_summary(root / ref.path, root)
        check_summary(new, ref)


if __name__ == "__main__":
    main()
