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
"""RepRep wrapper for typst.

This wrapper extracts relevant information from a typst build
to inform StepUp of input files used or needed.

This is tested with Typst 0.14.
A limitation of typst is that it will fail after the first missing file it requires,
making it inefficient to plan ahead and build all missing required inputs early.
"""

import argparse
import contextlib
import json
import shlex
import sys

from path import Path, TempDir

from stepup.core.api import amend, getenv
from stepup.core.utils import filter_dependencies
from stepup.core.worker import WorkThread

from .make_inventory import write_inventory


def main(argv: list[str] | None = None, work_thread: WorkThread | None = None):
    """Main program."""
    args = parse_args(argv)
    if work_thread is None:
        work_thread = WorkThread("stub")

    if not args.path_typ.endswith(".typ"):
        raise ValueError("The Typst source must have extension .typ")
    if not (args.path_out is None or args.path_out.suffix in (".pdf", ".png", ".svg", ".html")):
        raise ValueError("The Typst output must be a PDF, PNG, SVG, or HTML file.")

    # Get Typst executable and prepare some arguments that
    if args.typst is None:
        args.typst = getenv("REPREP_TYPST", "typst")

    # Prepare the command to run Typst
    typargs = [args.typst, "compile", args.path_typ]
    if args.path_out is not None:
        typargs.append(args.path_out)
    else:
        args.path_out = Path(args.path_typ[:-4] + ".pdf")
    if args.path_out.suffix == ".png":
        resolution = args.resolution
        if resolution is None:
            resolution = int(getenv("REPREP_TYPST_RESOLUTION", "144"))
        typargs.append(f"--ppi={resolution}")
    elif args.path_out.suffix == ".html":
        typargs.append("--features=html")
    for keyval in args.sysinp:
        typargs.append("--input")
        typargs.append(keyval)
    if len(args.typst_args) == 0:
        args.typst_args = shlex.split(getenv("REPREP_TYPST_ARGS", ""))
    typargs.extend(args.typst_args)

    with contextlib.ExitStack() as stack:
        if args.keep_deps:
            # Remove any existing make-deps output from a previous run.
            path_deps = args.path_typ.with_suffix(".deps.json")
            path_deps.remove_p()
        else:
            # Use a temporary file for the make-deps output.
            path_deps = stack.enter_context(TempDir()) / "typst.deps.json"
        typargs.extend(["--deps", path_deps, "--deps-format", "json"])

        # Run typst compile
        returncode, stdout, stderr = work_thread.runsh(shlex.join(typargs))
        print(stdout)
        # Assume there is a single output file, which is the one specified.
        # This is not correct when there are multiple outputs, e.g. as with SVG and PNG outputs.
        # Get required input files from the dependency file.
        if path_deps.is_file():
            with open(path_deps) as fh:
                depinfo = json.load(fh)
            inp_paths = depinfo["inputs"]
            out_paths = depinfo["outputs"]
        else:
            print(f"Dependency file not created: {path_deps}.", file=sys.stderr)
            out_paths = []
            inp_paths = []

    sys.stderr.write(stderr)
    inp_paths = filter_dependencies(inp_paths)
    amend(inp=inp_paths)

    # Write inventory
    if args.inventory is not None:
        inventory_paths = sorted(inp_paths) + sorted(out_paths)
        write_inventory(args.inventory, inventory_paths, do_amend=False)

    # If the output path contains placeholders `{p}`, `{0p}`, or `{t}`,
    # we need to amend the output.
    if any(p in args.path_out for p in ("{p}", "{0p}", "{t}")):
        amend(out=out_paths)

    if returncode != 0:
        # Only use sys.exit in cases of an error,
        # so other programs may call this function without exiting.
        sys.exit(returncode)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-compile-typst",
        description="Compile a Typst document and extract input and output info.",
    )
    parser.add_argument("path_typ", type=Path, help="The main typst source file.")
    parser.add_argument(
        "--out", dest="path_out", type=Path, help="The PDF/PNG/SVG output argument."
    )
    parser.add_argument(
        "--resolution",
        type=int,
        help="The resolution in DPI for PNG output. "
        "Defaults to ${REPREP_TYPST_RESOLUTION} or 144 if the variable is not defined.",
    )
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
    parser.add_argument(
        "--inventory",
        type=Path,
        help="Write an inventory with all inputs and outputs, useful for archiving.",
    )
    parser.add_argument(
        "--sysinp",
        nargs="+",
        help="These key=value inputs to be passed to typst with `--input key=val."
        "Multiple key=value pairs are allowed after a single --sysinp.",
        default=(),
    )
    parser.add_argument(
        "typst_args",
        nargs="*",
        help="Additional arguments to be passed to typst. "
        "The defaults is `${REPREP_TYPST_ARGS}`, if the environment variable is defined.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
