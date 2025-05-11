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
"""Checking of inventory files."""

import argparse
import sys
from collections.abc import Iterator

from path import Path

from .inventory import FileSummary, check_summary, get_summary, parse_summary

__all__ = ("check_inventory", "iter_inventory", "main")


def main(argv: list[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="rr-check-inventory", description="Check an inventory.txt."
    )
    add_parser_args(parser)
    args = parser.parse_args(argv)
    if not args.inventory_txt.endswith(".txt"):
        raise ValueError("The inventory file must end with .txt")
    check_inventory(args.inventory_txt)


def add_parser_args(parser: argparse.ArgumentParser):
    """Define command-line arguments."""
    parser.add_argument("inventory_txt", help="An inventory.txt file generated with RepRep")


def check_subcommand(subparser: argparse.ArgumentParser) -> callable:
    """Add subcommand to check inventory."""
    parser = subparser.add_parser(
        "check-inventory",
        help="Check the inventory file.",
    )
    add_parser_args(parser)
    return check_tool


def check_tool(args: argparse.Namespace) -> int:
    """Check the inventory file."""
    check_inventory(args.inventory_txt)
    return 0


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
    sys.exit(main(sys.argv))
