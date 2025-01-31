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
"""RepRep wrapper for typst.

This wrapper extracts relevant information from a typst build
to inform StepUp of input files used or needed.

This is tested with Typst 0.12.
A current limitation of typst is that it will fail after the first missing file it requires,
making it inefficient to plan ahead and build all missing required inputs early.
"""

import argparse
import contextlib
import shlex
import subprocess
import sys

from path import Path, TempDir

from stepup.core.api import amend, getenv
from stepup.core.utils import myrelpath


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)

    if not args.path_typ.endswith(".typ"):
        raise ValueError("The Typst source must have extension .typ.")

    # Get Typst executable
    if args.typst is None:
        args.typst = getenv("REPREP_TYPST", "typst")

    with contextlib.ExitStack() as stack:
        if args.keep_deps:
            # Remove any existing make-deps output from a previous run.
            path_dep = Path(args.path_typ[:-4] + ".dep")
            path_dep.remove_p()
        else:
            # Use a temporary file for the make-deps output.
            path_dep = stack.enter_context(TempDir()) / "typst.dep"

        # Run typst compile
        cp = subprocess.run(
            [args.typst, "compile", args.path_typ, "--make-deps", path_dep],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        # Get existing input files from the dependency file and amend.
        # Note that the deps file does not escape colons in paths,
        # so the code below assumes one never uses colons in paths.
        inp_paths = []
        if path_dep.is_file():
            with open(path_dep) as fh:
                _, deps = fh.read().split(":", 1)
                inp_paths.extend(args.path_typ.parent / p for p in shlex.split(deps))

    # Look for missing input files in the standard error stream and amend them.
    if cp.returncode != 0:
        lead = "error: file not found (searched at "
        inp_paths.extend(
            myrelpath(line[len(lead) : -1])
            for line in cp.stderr.decode().splitlines()
            if line.startswith(lead)
        )
    sys.stderr.write(cp.stderr.decode())
    amend(inp=inp_paths)
    sys.exit(cp.returncode)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-typst",
        description="Compile a Typst document and extract input and output info.",
    )
    parser.add_argument("path_typ", type=Path, help="The main typst source file.")
    parser.add_argument(
        "--typst",
        help="The Typst executable. "
        "The default is ${REPREP_TYPST} or typst if the variable is not defined.",
    )
    parser.add_argument(
        "--keep-deps",
        help="Keep the dependency file after the compilation. "
        "The default is to use a temporary file, which is removed after it is processed.",
        action="store_true",
        default=False,
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
