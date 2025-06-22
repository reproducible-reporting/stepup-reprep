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
"""RepRep Wrapper for LaTeX."""

import argparse
import contextlib
import shlex
import sys

from path import Path

from stepup.core.api import amend, getenv
from stepup.core.hash import compute_file_digest
from stepup.core.utils import filter_dependencies, mynormpath
from stepup.core.worker import WorkThread

from .bibtex_log import parse_bibtex_log
from .latex_deps import scan_latex_deps
from .latex_log import parse_latex_log
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
    stem = fn_tex[:-4]
    path_aux = workdir / f"{stem}.aux"

    # Remove existing outputs from a previous run, which could potentially
    # conflict with the new tex source files. In 99% of the cases, this is
    # not a problem, but sometimes LaTeX chokes on remnants in old outputs.
    exts_to_remove = ["log", "aux", "blg", "fls", "out", "toc", "nlo", "synctex"]
    if args.run_bibtex:
        exts_to_remove.append("bbl")
    for ext in exts_to_remove:
        (workdir / f"{stem}.{ext}").remove_p()

    # Detect additional inputs
    inp, bib, out, vol = scan_latex_deps(fn_tex)

    # Get LaTeX executable
    if args.latex is None:
        args.latex = getenv("REPREP_LATEX", "pdflatex")

    aux_digest_hist = []
    if len(bib) == 0:
        amend(inp=inp, out=out, vol=vol)
        inventory_files = [*inp, *out]
    elif args.run_bibtex:
        # Get other executables and files
        if args.bibtex is None:
            args.bibtex = getenv("REPREP_BIBTEX", "bibtex")

        amend(inp=inp + bib, out=[f"{stem}.bbl", *out], vol=vol)
        inventory_files = [*inp, *bib, f"{stem}.bbl", *out]

        # Run LaTeX once to generate the .aux file
        with contextlib.chdir(workdir):
            returncode, _, _ = work_thread.runsh(
                f"{shlex.quote(args.latex)} -recorder -interaction=errorstopmode -draftmode {stem}"
            )
        if returncode != 0:
            path_log = workdir / f"{stem}.log"
            error_info = parse_latex_log(path_log)
            error_info.print(path_log)
            sys.exit(1)

        aux_digest_hist.append(compute_file_digest(path_aux))

        # BibTeX
        with contextlib.chdir(workdir):
            returncode, _, _ = work_thread.runsh(f"{shlex.quote(args.bibtex)} {stem}")
        if returncode != 0:
            path_blg = workdir / f"{stem}.blg"
            error_info = parse_bibtex_log(path_blg)
            error_info.print(path_blg)
            sys.exit(1)
    else:
        amend(inp=[*inp, f"{stem}.bbl"], out=out, vol=vol)
        inventory_files = [*inp, f"{stem}.bbl", *out]

    # Keep running LaTeX until the .aux file converges.
    for _ in range(args.maxrep):
        with contextlib.chdir(workdir):
            returncode, _, _ = work_thread.runsh(
                f"{shlex.quote(args.latex)} -recorder -interaction=errorstopmode {stem}"
            )
        path_log = workdir / f"{stem}.log"
        error_info = parse_latex_log(path_log)
        if returncode != 0:
            error_info.print(path_log)
            sys.exit(1)
        aux_digest_hist.append(compute_file_digest(path_aux))
        if len(aux_digest_hist) > 1 and aux_digest_hist[-1] == aux_digest_hist[-2]:
            break
    else:
        print(
            f"\033[1;31;40mAux file did not converge in {args.maxrep} iterations!\033[0;0m",
            file=sys.stderr,
        )
        print(path_aux, file=sys.stderr)
        for digest in aux_digest_hist:
            print(digest.hex(), file=sys.stderr)
        sys.exit(1)

    # Write inventory
    inventory_files.extend([f"{stem}.tex", f"{stem}.aux", f"{stem}.pdf"])
    if args.inventory is not None:
        write_inventory(args.inventory, inventory_files, do_amend=False)

    # Look for input files and output files from the fls file.
    # These are usually worth tracking, but are not needed for the inventory file.
    fls_inp = set()
    fls_vol = set()
    with open(f"{stem}.fls") as fh:
        for line in fh:
            if line.startswith("INPUT "):
                path = mynormpath(Path(line[6:].strip()))
                if not (path in inventory_files or path == args.inventory):
                    fls_inp.add(path)
            elif line.startswith("OUTPUT "):
                path = mynormpath(Path(line[7:].strip()))
                if not (path in inventory_files or path == args.inventory):
                    fls_vol.add(path)
    fls_inp.difference_update(fls_vol)
    # Both inputs and outputs must be filtered because, strangely,
    # LaTeX sometimes outputs files in the weirdest places, e.g. in the TEXMF tree.
    amend(inp=filter_dependencies(fls_inp), vol=filter_dependencies(fls_vol))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-compile-latex",
        description="Compile a LaTeX document and extract input and output info.",
    )
    parser.add_argument("path_tex", type=Path, help="The main LaTeX source file.")
    parser.add_argument(
        "-m",
        "--maxrep",
        default=5,
        type=int,
        help="The maximum number of LaTeX recompilations (not including the one for BibTeX).",
    )
    parser.add_argument(
        "--latex",
        help="The LaTeX executable. "
        "The default is ${REPREP_LATEX} or pdflatex if the variable is not defined.",
    )
    parser.add_argument(
        "--run-bibtex",
        dest="run_bibtex",
        default=False,
        action="store_true",
        help="Run bibtex.",
    )
    parser.add_argument(
        "--bibtex",
        help="The BibTeX executable. "
        "The default is ${REPREP_BIBTEX} or bibtex if the variable is not defined.",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        help="Write an inventory with all inputs and outputs, useful for archiving.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
