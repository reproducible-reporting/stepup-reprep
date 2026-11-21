# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Create inventory files.

There are two kinds of inventory files:

- `inventory.def` defines rules to include and exclude files.
- `inventory.jsonl` is the result of processing an `inventory.def` file with this script,
  or of listing the files on the command line.
  It describes every individual file, with its size and digest,
  in the format defined in `stepup.reprep.inventory`.
"""

import argparse
import contextlib
import shlex
import sqlite3
import sys
from collections.abc import Collection, Sequence

from stepup.core.api import amend
from stepup.core.enums import FileState
from stepup.core.extapi import run_subprocess
from stepup.core.nglob import NamedGlob
from stepup.core.path import Path, StrPath
from stepup.core.platform.oscompat import file_modes_available

from .inventory import (
    HASH_ALGORITHMS,
    InventoryHeader,
    compute_record,
    format_header,
    format_record,
)

__all__ = ("main", "write_inventory")


def main(argv: Sequence[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="srr-make-inventory", description="Make an inventory file in JSON Lines format."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files to include in the inventory, in the given order. "
        "They come before the files matched by the inventory definition, if any.",
    )
    parser.add_argument("-i", "--inventory-def", help="An inventory definition file.", default=None)
    parser.add_argument(
        "-o",
        "--output",
        help="The inventory file to write, with suffix .jsonl. "
        "It is optional with -i X.def, in which case X.jsonl is written.",
        default=None,
    )
    parser.add_argument(
        "--hash",
        dest="hash_algorithm",
        choices=HASH_ALGORITHMS,
        default="md5",
        help="The hash algorithm for the digests of the files. [default=%(default)s]",
    )
    parser.add_argument(
        "--mode",
        default=False,
        action="store_true",
        help="Also record the permission bits of the files.",
    )
    args = parser.parse_args(argv)
    if args.inventory_def is None:
        if len(args.paths) == 0:
            parser.error("At least -i inventory.def or a list of files is needed as input.")
        if args.output is None:
            parser.error("Without -i inventory.def, the -o option is required.")
    make_inventory(args)


def make_inventory(args: argparse.Namespace):
    if args.inventory_def is not None:
        if not args.inventory_def.endswith(".def"):
            raise ValueError("The inventory definition file must end with .def")
        if args.output is None:
            args.output = args.inventory_def[:-4] + ".jsonl"
        elif Path(args.output).parent != Path(args.inventory_def).parent:
            raise ValueError(
                "The inventory definition and the output must have the same parent directory."
            )

    path_out = Path(args.output)
    paths = list(args.paths)
    if args.inventory_def is not None:
        root = path_out.parent.normpath()
        with open(args.inventory_def, encoding="utf-8") as fh:
            lines = fh.readlines()
        with contextlib.chdir(root):
            paths_def = parse_inventory_def(lines)
        paths.extend(root / path for path in sorted(paths_def))
    write_inventory(path_out, paths, hash_algorithm=args.hash_algorithm, mode=args.mode)


def get_file_list_nglob(i: int, args: list[str]) -> Collection[Path]:
    if len(args) == 0:
        raise ValueError(
            f"Error on line {i} of the inventory definition: include or exclude has no arguments."
        )
    paths = []
    for arg in args:
        ng = NamedGlob(arg)
        ng.glob()
        paths.extend(ng.files())
    return paths


def get_file_list_git(i: int, args: list[str]) -> Collection[Path]:
    cp = run_subprocess(shlex.join(["git", "ls-files", *args]))
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
    paths_graph_db = []
    for arg in args[1:]:
        ng = NamedGlob(arg)
        ng.glob()
        paths_graph_db.extend(ng.files())
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


def write_inventory(
    path_out: StrPath,
    paths: Sequence[StrPath],
    *,
    hash_algorithm: str = "md5",
    mode: bool = False,
    do_amend: bool = True,
):
    """Write an inventory file.

    The files are hashed and written one at a time, so only the list of paths is kept in memory.

    Parameters
    ----------
    path_out
        The location of the inventory file to be written, with suffix `.jsonl`.
    paths
        The paths to be included in the inventory, in the order of the records.
        These must be paths relative to the current working directory.
        They will be written to the inventory file
        as paths relative to the parent of the inventory file.
        When two of them are the same after this conversion, only the first one is kept.
    hash_algorithm
        The name of the `hashlib` algorithm that digests the regular files.
    mode
        When True, the permission bits of the regular files are recorded.
        A warning is printed on a platform where files have no permission bits.
    do_amend
        When True, `paths` are amended as inputs of the current step,
        so that the inventory is rebuilt when they change.
        Set this to False when the step already declares these files itself,
        because the extra amendment may then introduce a cyclic dependency.
    """
    path_out = Path(path_out)
    if not path_out.endswith(".jsonl"):
        raise ValueError(f"The inventory file must have a `.jsonl` extension. Got {path_out}")
    header = InventoryHeader(hash_algorithm, mode)
    if mode and not file_modes_available():
        print(
            "WARNING: Files have no permission bits on this platform. "
            "The recorded modes are derived from the read-only attribute and the file name.",
            file=sys.stderr,
        )

    root = path_out.parent.normpath()
    unique_paths = []
    seen = set()
    for path in paths:
        path = Path(path)
        relpath = path.relpath(root).normpath()
        if relpath not in seen:
            seen.add(relpath)
            unique_paths.append(path)

    if do_amend:
        for path in unique_paths:
            if path.endswith("/") or path.is_dir():
                raise ValueError(f"Directories are not allowed in the inventory: {path}")
        amend(inp=unique_paths)

    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        print(format_header(header), file=fh)
        for path in unique_paths:
            record = compute_record(path, root, hash_algorithm, mode)
            print(format_record(record, header), file=fh)


if __name__ == "__main__":
    sys.exit(main())
