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
import tempfile
from collections.abc import Sequence

from stepup.core.api import amend, getenv
from stepup.core.extapi import filter_dependencies, run_subprocess
from stepup.core.path import Path
from stepup.core.utils import to_bool

from .argparse_compat import parse_passthrough_args
from .make_inventory import write_inventory

__all__ = ("main",)

MISSING_INPUT_PATTERN = re.compile(r"^error: .*?`([^`]+)' not found", flags=re.MULTILINE)
r"""Pattern for the missing input files that Tectonic reports on the standard error stream.

Only lines starting with `error: ` are considered.
As of Tectonic 0.17, a halted run also dumps the engine transcript to the same stream,
and the definition of `\@missingfileerror` quoted in it matches the same phrase.
"""


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

    # Prepare the command to run Tectonic, which runs in `workdir`.
    tectonic_args = [args.tectonic, "-c", "minimal", fn_tex]
    if args.outdir is not None:
        # An absolute path is kept, because it may lie on another drive than `workdir` on Windows.
        outdir = args.outdir if args.outdir.isabs() else args.outdir.relpath(workdir)
        tectonic_args.extend(["--outdir", outdir])
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
            path_dep = Path(args.path_tex.with_suffix(".dep")).normpath()
            path_dep.remove_p()
            if do_amend_deps:
                amend(out=path_dep)
            arg_dep = Path(fn_tex).with_suffix(".dep")
        else:
            # Use a temporary file for the make-deps output.
            path_dep = Path(stack.enter_context(tempfile.TemporaryDirectory())) / "tectonic.dep"
            arg_dep = path_dep
        tectonic_args.extend(["--makefile-rules", arg_dep])

        # Run Tectonic in the directory of the tex file
        cp = run_subprocess(shlex.join(tectonic_args), workdir=workdir, check=False)
        sys.stdout.write(cp.stdout)
        # Get existing input files from the dependency file and amend.
        inp_paths = []
        out_paths = []
        if path_dep.is_file():
            with open(path_dep, encoding="utf-8") as fh:
                dep_out, dep_inp = parse_makefile_rules(fh.read())
            out_paths.extend(workdir / path for path in dep_out)
            inp_paths.extend(workdir / path for path in dep_inp)
        else:
            print(f"Dependency file not created: {path_dep}.", file=sys.stderr)

    # Look for missing input files in the standard error stream and amend them.
    if cp.returncode != 0:
        inp_paths.extend(workdir / m.group(1) for m in MISSING_INPUT_PATTERN.finditer(cp.stderr))
    sys.stderr.write(cp.stderr)
    inp_paths = filter_dependencies(inp_paths)
    amend(inp=inp_paths)

    if args.inventory is not None:
        inventory_paths = sorted(inp_paths) + out_paths
        write_inventory(args.inventory, inventory_paths, do_amend=False)

    if cp.returncode != 0:
        sys.exit(cp.returncode)


def parse_makefile_rules(text: str) -> tuple[list[str], list[str]]:
    """Parse the Makefile rules written by Tectonic with `--makefile-rules`.

    As of Tectonic 0.17, the file names in these rules are neither quoted nor escaped,
    and they contain the native path separator, which is a backslash on Windows.
    Hence, file names with spaces are not supported.
    Outputs and inputs are separated by a colon followed by whitespace,
    so that the colon of a drive letter on Windows is not mistaken for the separator.

    Parameters
    ----------
    text
        The contents of the file with Makefile rules.

    Returns
    -------
    out_paths
        The outputs written by Tectonic.
    inp_paths
        The inputs read by Tectonic.
    """
    dep_out, dep_inp = re.split(r":\s", text.replace("\\\n", " "), maxsplit=1)
    return dep_out.split(), dep_inp.split()


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
        "--outdir",
        type=Path,
        help="The directory in which to write the PDF. "
        "The default is the directory of the LaTeX source.",
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
    return parse_passthrough_args(parser, argv)


if __name__ == "__main__":
    sys.exit(main())
