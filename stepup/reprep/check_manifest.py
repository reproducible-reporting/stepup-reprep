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
"""Checking of MANIFEST files.

There are two kinds of MANIFEST files:

- ``MANIFEST.in`` contains rules to select or ignore files to be included into an archive.
- ``MANIFEST.txt`` is the result of a processing a ``MANIFEST.in`` file with this script.
  It contains every individual file, together with its size in bytes and its blake2b hexdigest.
"""

import argparse
import sys
from collections.abc import Iterator

from path import Path

from stepup.core.hash import compute_file_digest

__all__ = ("main", "iter_manifest", "check_manifest")


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if not args.manifest_txt.endswith(".txt"):
        raise ValueError("The manifest output file must end with .txt")
    check_manifest(args.manifest_txt)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-check-manifest", description="Check a MANIFEST.txt."
    )
    parser.add_argument("manifest_txt", help="A MANIFEST.txt file generated with RepRep")
    args = parser.parse_args(argv)
    return args


def iter_manifest(path_manifest: str) -> Iterator[tuple[int, bytes, str]]:
    root = path_manifest.parent.normpath()
    with open(path_manifest) as fh:
        for iline, line in enumerate(fh):
            if len(line) < 146:
                raise ValueError(f"Line {iline} too short in {path_manifest}")
            size = int(line[:15])
            digest = bytes.fromhex(line[16:144])
            path = line[145:].strip()
            yield size, digest, root / path


def check_manifest(path_manifest: str):
    path_manifest = Path(path_manifest)
    for size, digest, path in iter_manifest(path_manifest):
        actual_size = Path(path).getsize()
        if size != actual_size:
            raise ValueError(f"File size should be {size} but got {actual_size}: {path}")
        actual_digest = compute_file_digest(path)
        if digest != actual_digest:
            raise ValueError(f"File digest mismatch: {path}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
