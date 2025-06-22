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
"""Create inventory files.

There are two kinds of inventory files:

- ``inventory.def`` defines rules to include and exclude files to be archived.
- ``inventory.txt`` is the result of a processing a ``inventory.def`` file with this script.
  It contains every individual file, together with its size in bytes and its blake2b hexdigest.
"""

import argparse
import contextlib
import shlex
import sqlite3
import subprocess
import sys
from collections.abc import Collection

from path import Path

from stepup.core.api import amend
from stepup.core.file import FileState
from stepup.core.nglob import NGlobMulti

from .inventory import format_summary, get_summary

__all__ = ("main", "write_inventory")


def main(argv: list[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="rr-make-inventory", description="Make an inventory.txt file."
    )
    add_parser_args(parser)
    args = parser.parse_args(argv)
    make_inventory(args)


def add_parser_args(parser: argparse.ArgumentParser):
    """Define command-line arguments."""
    parser.add_argument(
        "paths",
        nargs="*",
        help="File to include in the inventory. "
        "(Added after porcessing the inventory definition if any.)",
    )
    parser.add_argument("-i", "--inventory-def", help="An inventory definition file.", default=None)
    parser.add_argument("-o", "--inventory-txt", help="An inventory output file.", default=None)


def make_subcommand(subparser: argparse.ArgumentParser) -> callable:
    """Create a subcommand for the command line interface."""
    parser = subparser.add_parser(
        "make-inventory",
        help="Create an inventory.txt file.",
    )
    add_parser_args(parser)
    return make_tool


def make_tool(args: argparse.Namespace) -> int:
    """Create an inventory.txt file."""
    make_inventory(args)
    return 0


def make_inventory(args: argparse.Namespace):
    # Check arguments
    if args.inventory_def is None:
        if len(args.paths) == 0:
            raise ValueError("At least inventory.def or a list of files are needed as input.")
        if args.inventory_txt is None:
            raise ValueError("Whithout -i inventory.def, the -o option is no longer optional.")
    else:
        if not args.inventory_def.endswith(".def"):
            raise ValueError("The inventory defintion file must end with .def")
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


def get_file_list_nglob(i: int, args: list[str]) -> Collection[Path]:
    if len(args) == 0:
        raise ValueError(
            f"Error on line {i} of the inventory definition: include or exclude has no arguments."
        )
    ngm = NGlobMulti.from_patterns(args)
    ngm.glob()
    return ngm.files()


def get_file_list_git(i: int, args: list[str]) -> Collection[Path]:
    cp = subprocess.run(
        ["git", "ls-files", *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        encoding="utf-8",
    )
    return [Path(line.strip()) for line in cp.stdout.splitlines()]


def get_file_list_workflow(i: int, args: list[str]) -> Collection[Path]:
    """Get a list of files from a StepUp graph.db workflow file.

    There must be at least two arguments: the state and one or more patterns of graph.db files.
    """
    if len(args) < 2:
        raise ValueError(
            f"Error on line {i} of the inventory definition: Expecting at least two arguments."
        )
    state = FileState[args[0]]
    ngm = NGlobMulti.from_patterns(args[1:])
    ngm.glob()
    paths_graph_db = ngm.files()
    if len(paths_graph_db) == 0:
        raise ValueError(
            f"Error on line {i} of the inventory definition: no matching graph.db workflow files."
        )
    paths = set()
    for path_graph_db in paths_graph_db:
        if path_graph_db.parent.name != ".stepup":
            raise ValueError("A graph.db file must be in a .stepup directory.")
        root = path_graph_db.parent.parent
        con = sqlite3.connect(f"file:{path_graph_db}?mode=ro", uri=True)
        sql = "SELECT label FROM node JOIN file ON node.i = file.node WHERE state = ?"
        for (path,) in con.execute(sql, (state.value,)):
            if not path.endswith("/"):
                paths.add(root / path)
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
        A list of single lines from an inventory definition file.
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
        new_paths = [path for path in new_paths if not path.is_dir()]
        if len(new_paths) == 0:
            raise ValueError(f"Line {i} matches no paths: {line}")
        if action == "include":
            paths.update(new_paths)
        else:
            paths.difference_update(new_paths)
    return paths


def write_inventory(path_txt: str, paths: Collection[str], do_amend: bool = True):
    """Write an inventory file.

    Parameters
    ----------
    path_txt
        The location of the inventory file to be written.
    paths
        A collection of paths to be included in the inventory.
        These must be paths relative to the current working directory.
        They will be written to the inventory file
        as paths relative to the parent of the inventory file.
    """
    # Amend all paths included in the inventory file as inputs.
    # This is needed to ensure that the inventory is rebuilt when the paths change.
    # Other actions calling this function may not want this,
    # because they already take care of file dependencies and amendments
    # may then cause cyclic dependencies.
    if do_amend:
        inp_paths = []
        for path in paths:
            path = Path(path)
            if path.is_dir() and not path.endswith("/"):
                path = path / ""
            inp_paths.append(path)
        amend(inp=inp_paths)

    # Write the inventory file.
    path_txt = Path(path_txt)
    root = path_txt.parent.normpath()
    with open(path_txt, "w") as fh:
        for path in paths:
            print(format_summary(get_summary(path, root)), file=fh)


if __name__ == "__main__":
    main(sys.argv[1:])
