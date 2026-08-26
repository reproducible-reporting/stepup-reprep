# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""RepRep Wrapper for the Tectonic LaTeX compiler.

The Tectonic command-line interface deviates quite a bit from the usual LaTeX compilers,
so it is easier to have a separate wrapper for it.
"""

import argparse
import contextlib
import re
import shlex
import sys
from collections.abc import Sequence

from path import Path, TempDir

from stepup.core.api import amend, getenv
from stepup.core.extapi import filter_dependencies, run_subprocess
from stepup.core.utils import to_bool

from .make_inventory import write_inventory

__all__ = ("main",)


def main(argv: Sequence[str] | None = None) -> None:
    """Main program."""
    args = parse_args(argv)

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

    # Prepare keep_deps argument
    do_amend_deps = False
    if args.keep_deps is None:
        args.keep_deps = to_bool(getenv("REPREP_TECTONIC_KEEP_DEPS", "0"))
        if args.keep_deps:
            do_amend_deps = True

    with contextlib.ExitStack() as stack:
        if args.keep_deps:
            # Remove any existing make-deps output from a previous run.
            path_dep = Path(args.path_tex.with_suffix(".dep"))
            path_dep.remove_p()
            if do_amend_deps:
                amend(out=path_dep)
        else:
            # Use a temporary file for the make-deps output.
            path_dep = stack.enter_context(TempDir()) / "tectonic.dep"
        tectonic_args.extend(["--makefile-rules", path_dep])

        # Run Tectonic in the directory of the tex file
        with contextlib.chdir(workdir):
            cp = run_subprocess(shlex.join(tectonic_args), check=False)
        sys.stdout.write(cp.stdout)
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
    if cp.returncode != 0:
        inp_paths.extend(
            workdir / m.group(1)
            for m in re.finditer(r"`([^`]+)' not found", cp.stderr, flags=re.MULTILINE)
        )
    sys.stderr.write(cp.stderr)
    inp_paths = filter_dependencies(inp_paths)
    amend(inp=inp_paths)

    if args.inventory is not None:
        inventory_paths = sorted(inp_paths) + out_paths
        write_inventory(args.inventory, inventory_paths, do_amend=False)

    if cp.returncode != 0:
        sys.exit(cp.returncode)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-compile-tectonic",
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
        action=argparse.BooleanOptionalAction,
        default=None,
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
    main()
