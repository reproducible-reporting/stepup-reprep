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
"""RepRep Wrapper for the Tectonic LaTeX compiler.

The Tectonic command-line interface deviates quite a bit from the usual LaTeX compilers,
so it is easier to have a separate wrapper for it.
"""

import argparse
import contextlib
import re
import shlex
import sys

from path import Path, TempDir

from stepup.core.api import amend, getenv
from stepup.core.utils import filter_dependencies
from stepup.core.worker import WorkThread

from .make_inventory import write_inventory


def main(argv: list[str] | None = None, work_thread: WorkThread | None = None) -> None:
    """Main program."""
    args = parse_args(argv)
    if work_thread is None:
        work_thread = WorkThread("stub")

    workdir, fn_tex = args.path_tex.splitpath()
    workdir = workdir.normpath()
    if not fn_tex.endswith(".tex"):
        raise ValueError("The LaTeX source must have extension .tex")

    # Get the Tectonic executable
    if args.tectonic is None:
        args.tectonic = getenv("REPREP_TECTONIC", "tectonic")

    # Prepare the command to run Tectonic
    tectonic_args = [args.tectonic, "-c", "minimal", args.path_tex]
    if len(args.tectonic_args) == 0:
        args.tectonic_args = shlex.split(getenv("REPREP_TECTONIC_ARGS", ""))
    tectonic_args.extend(args.tectonic_args)

    with contextlib.ExitStack() as stack:
        if args.keep_deps:
            # Remove any existing make-deps output from a previous run.
            path_dep = Path(args.path_tex.with_suffix(".dep"))
            path_dep.remove_p()
        else:
            # Use a temporary file for the make-deps output.
            path_dep = stack.enter_context(TempDir()) / "tectonic.dep"
        tectonic_args.extend(["--makefile-rules", path_dep])

        # Run Tectonic in the directory of the tex file
        with contextlib.chdir(workdir):
            returncode, stdout, stderr = work_thread.runsh(shlex.join(tectonic_args))
        print(stdout)
        # Get existing input files from the dependency file and amend.
        # Note that the deps file does not escape colons in paths,
        # so the code below assumes one never uses colons in paths.
        inp_paths = []
        out_paths = []
        if path_dep.is_file():
            with open(path_dep) as fh:
                dep_out, dep_inp = fh.read().replace("\\\n", " ").split(":", 1)
                out_paths.extend(workdir / path for path in shlex.split(dep_out))
                inp_paths.extend(workdir / path for path in shlex.split(dep_inp))
        else:
            print(f"Dependency file not created: {path_dep}.", file=sys.stderr)

    # Look for missing input files in the standard error stream and amend them.
    if returncode != 0:
        inp_paths.extend(
            workdir / m.group(1)
            for m in re.finditer(r"`([^`]+)' not found", stderr, flags=re.MULTILINE)
        )
    sys.stderr.write(stderr)
    inp_paths = filter_dependencies(inp_paths)
    amend(inp=inp_paths)

    # Write inventory
    if args.inventory is not None:
        inventory_paths = sorted(inp_paths) + out_paths
        write_inventory(args.inventory, inventory_paths, do_amend=False)

    if returncode != 0:
        # Only use sys.exit in cases of an error,
        # so other programs may call this function without exiting.
        sys.exit(returncode)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-compile-tectonic",
        description="Compile a LaTeX document with Tectonic and deduce input and output info.",
    )
    parser.add_argument("path_tex", type=Path, help="The main LaTeX source file.")
    parser.add_argument(
        "-m",
        "--maxrep",
        default=6,
        type=int,
        help="The maximum number of LaTeX recompilations (not including the one for BibTeX).",
    )
    parser.add_argument(
        "--tectonic",
        help="The Tectonic executable. "
        "The default is ${REPREP_TECTONIC} or tectonic if the variable is not defined.",
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
        "tectonic_args",
        nargs="*",
        help="Additional arguments to be passed to tectonic. "
        "The defaults is `${REPREP_TECTONIC_ARGS}`, if the environment variable is defined.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
