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
"""Making of MANIFEST files.

There are two kinds of MANIFEST files:

- ``MANIFEST.in`` contains rules to select or ignore files to be included into an archive.
- ``MANIFEST.txt`` is the result of a processing a ``MANIFEST.in`` file with this script.
  It contains every individual file, together with its size in bytes and its blake2b hexdigest.
"""

import argparse
import contextlib
import sys
from collections.abc import Collection

from path import Path
from setuptools.command.egg_info import FileList

from stepup.core.hash import compute_file_digest

__all__ = ("main", "write_manifest")


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)

    # Check arguments
    if args.manifest_in is None:
        if len(args.paths) == 0:
            raise ValueError("At least MANIFEST.in or a list of files are needed as input.")
        if args.manifest_txt is None:
            raise ValueError("When no MANIFEST.in, the -o option is no longer optional.")
    else:
        if not args.manifest_in.endswith(".in"):
            raise ValueError("The manifest input file must end with .in")
        if args.manifest_txt is None:
            args.manifest_txt = args.manifest_in[:-3] + ".txt"
        elif Path(args.manifest_txt).parent != Path(args.manifest_in).parent:
            raise ValueError(
                "The MANIFEST.in and MANIFEST.txt files must have the same parent directory."
            )
    if not args.manifest_txt.endswith(".txt"):
        raise ValueError("The manifest output file must end with .txt")

    # Collect the complete list of files.
    path_manifest_txt = Path(args.manifest_txt)
    root = path_manifest_txt.parent.normpath()
    if args.manifest_in is None:
        paths = set()
    else:
        path_manifest_in = Path(args.manifest_in)
        with contextlib.chdir(root):
            filelist = FileList()
            with open(path_manifest_in.name) as f:
                for line in f:
                    line = line[: line.find("#")].strip()
                    if line != "":
                        filelist.process_template_line(line)
            paths = {root / file for file in filelist.files}
    paths.update(args.paths)
    write_manifest(path_manifest_txt, sorted(paths))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-make-manifest", description="Make a MANIFEST.txt."
    )
    parser.add_argument(
        "paths",
        nargs="*",
    )
    parser.add_argument(
        "-i", "--manifest-in", help="A MANIFEST.in file compatible with setuptools.", default=None
    )
    parser.add_argument("-o", "--manifest-txt", help="A MANIFEST.txt output file.", default=None)
    args = parser.parse_args(argv)
    return args


def write_manifest(path_manifest: str, paths: Collection[str]):
    path_manifest = Path(path_manifest)
    root = path_manifest.parent.normpath()
    with open(path_manifest, "w") as fh:
        for path in paths:
            path = Path(path)
            size = path.getsize()
            relpath = path.relpath(root)
            digest = compute_file_digest(path)
            print(f"{size:15d} {digest.hex()} {relpath}", file=fh)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
