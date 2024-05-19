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
"""Create inventory files.

There are two kinds of inventory files:

- ``inventory.def`` defines rules to include and exclude files to be archived.
- ``inventory.txt`` is the result of a processing a ``inventory.def`` file with this script.
  It contains every individual file, together with its size in bytes and its blake2b hexdigest.
"""

import argparse
import contextlib
import shlex
import subprocess
import sys
from collections.abc import Collection

from path import Path

from stepup.core.file import FileState
from stepup.core.nglob import NGlobMulti
from stepup.core.workflow import Workflow

from .inventory import format_summary, get_summary

__all__ = ("main", "write_inventory")


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)

    # Check arguments
    if args.inventory_def is None:
        if len(args.paths) == 0:
            raise ValueError("At least inventory.def or a list of files are needed as input.")
        if args.inventory_txt is None:
            raise ValueError("Whithout -i inventory.def, the -o option is no longer optional.")
    else:
        if not args.inventory_def.endswith(".def"):
            raise ValueError("The inventory input file must end with .def")
        if args.inventory_txt is None:
            args.inventory_txt = args.inventory_def[:-4] + ".txt"
        elif Path(args.inventory_txt).parent != Path(args.inventory_def).parent:
            raise ValueError(
                "The inventory_def and inventory_txt files must have the same parent directory."
            )
    if not args.inventory_txt.endswith(".txt"):
        raise ValueError("The inventory output file must end with .txt")

    # Collect the complete list of files.
    path_inventory_txt = Path(args.inventory_txt)
    root = path_inventory_txt.parent.normpath()
    if args.inventory_def is None:
        paths = set()
    else:
        with open(args.inventory_def) as fh:
            lines = fh.readlines()
        with contextlib.chdir(root):
            paths = {root / path for path in parse_inventory_def(lines)}
    paths.update(args.paths)
    write_inventory(path_inventory_txt, sorted(paths))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-make-inventory", description="Make an inventory.txt file."
    )
    parser.add_argument(
        "paths",
        nargs="*",
    )
    parser.add_argument("-i", "--inventory-def", help="An inventory input file.", default=None)
    parser.add_argument("-o", "--inventory-txt", help="An inventory output file.", default=None)
    args = parser.parse_args(argv)
    return args


def get_file_list_nglob(i: int, args: list[str]) -> Collection[str]:
    if len(args) == 0:
        raise ValueError(
            f"Error on line {i} of the inventory input: include or exclude has no arguments."
        )
    ngm = NGlobMulti.from_patterns(args)
    ngm.glob()
    return ngm.files()


def get_file_list_git(i: int, args: list[str]) -> Collection[str]:
    if len(args) != 0:
        raise ValueError(
            f"Error on line {i} of the inventory input: "
            "include-git and exclude-git take no arguments."
        )
    cp = subprocess.run(
        ["git", "ls-files"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        encoding="utf-8",
    )
    return [line.strip() for line in cp.stdout.splitlines()]


def get_file_list_workflow(i: int, args: list[str]) -> Collection[str]:
    if len(args) < 2:
        raise ValueError(
            f"Error on line {i} of the inventory input: Expecting at least two arguments."
        )
    state = FileState[args[0]]
    ngm = NGlobMulti.from_patterns(args[1:])
    ngm.glob()
    paths_workflow = ngm.files()
    if len(paths_workflow) == 0:
        raise ValueError(f"Error on line {i} of the inventory input: no matching workflow files.")
    paths = set()
    for path_workflow in paths_workflow:
        if not path_workflow.parent.name == ".stepup":
            raise ValueError("A workflow.mpk.xz file must be in a .stepup directory.")
        root = path_workflow.parent.parent
        workflow = Workflow.from_file(path_workflow)
        for file_key in workflow.file_states.inverse.get(state):
            if not file_key.endswith("/"):
                paths.add(root / file_key[5:])
    return paths


FILE_LIST_SOURCES = {
    "": get_file_list_nglob,
    "-git": get_file_list_git,
    "-workflow": get_file_list_workflow,
}


def parse_inventory_def(lines: list[str], paths: list[str] | None = None) -> set[str]:
    """Process lines from an inventory definition file.

    Parameters
    ----------
    lines
        A list of single lines from an inventory input file.
    paths
        A list of paths to use as a starting point, if any.
        When not given, this function starts from an empty list.

    Returns
    -------
    paths
        A set of paths obtained by processing the include and exclude commands.
        When an initial paths list is given, it is not altered.
    """
    paths = set() if paths is None else set(paths)
    for i, line in enumerate(lines):
        words = shlex.split(line, comments=True)
        if len(words) == 0:
            continue
        command = words[0]
        args = words[1:]
        action = command[:7].lower()
        if action not in ["include", "exclude"]:
            raise ValueError(f"Line {i} does not start with include or exclude: {line}")
        source = command[7:].lower()
        file_list_function = FILE_LIST_SOURCES.get(source)
        if file_list_function is None:
            raise ValueError(f"Unsupported command on line {i}: {command}")
        new_paths = file_list_function(i, args)
        if len(new_paths) == 0:
            raise ValueError(f"Line {i} does not provide any paths: {line}")
        if action == "include":
            paths.update(new_paths)
        else:
            paths.difference_update(new_paths)
    return paths


def write_inventory(path_txt: str, paths: Collection[str]):
    path_txt = Path(path_txt)
    root = path_txt.parent.normpath()
    with open(path_txt, "w") as fh:
        for path in paths:
            print(format_summary(get_summary(path, root)), file=fh)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
