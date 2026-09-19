# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""RepRep Wrapper for LaTeX."""

import argparse
import shlex
import sys
from collections.abc import Sequence

from path import Path

from stepup.core.api import amend, getenv
from stepup.core.extapi import filter_dependencies, run_subprocess
from stepup.core.hash import compute_file_digest

from .bibtex_log import parse_bibtex_log
from .latex_deps import scan_latex_deps
from .latex_log import parse_latex_log
from .make_inventory import write_inventory

__all__ = ("main",)


def main(argv: Sequence[str] | None = None) -> None:
    """Main program."""
    args = parse_args(argv)

    workdir, fn_tex = args.path_tex.splitpath()
    workdir = workdir.normpath()
    if not fn_tex.endswith(".tex"):
        raise ValueError("The LaTeX source must have extension .tex")
    # LaTeX runs in `workdir`, where it only needs `stem`.
    # Paths in this process are relative to the current directory and use `path_stem`.
    stem = fn_tex[:-4]
    path_stem = (workdir / stem).normpath()
    path_aux = Path(f"{path_stem}.aux")
    path_bbl = Path(f"{path_stem}.bbl")

    # Remove existing outputs from a previous run,
    # which could potentially conflict with the new tex source files.
    # In 99% of the cases, this is not a problem,
    # but sometimes LaTeX chokes on remnants in old outputs.
    exts_to_remove = ["log", "aux", "blg", "fls", "out", "toc", "nlo", "synctex"]
    if args.run_bibtex:
        exts_to_remove.append("bbl")
    for ext in exts_to_remove:
        Path(f"{path_stem}.{ext}").remove_p()

    inp, bib, out, vol = scan_latex_deps(args.path_tex, do_amend=False)

    if args.latex is None:
        args.latex = getenv("REPREP_LATEX", "pdflatex")

    aux_digest_hist = []
    if len(bib) == 0:
        amend(inp=inp, out=out, vol=vol)
        inventory_files = [*inp, *out]
    elif args.run_bibtex:
        if args.bibtex is None:
            args.bibtex = getenv("REPREP_BIBTEX", "bibtex")

        amend(inp=inp + bib, out=[path_bbl, *out], vol=vol)
        inventory_files = [*inp, *bib, path_bbl, *out]

        # Run LaTeX once to generate the .aux file
        cp = run_subprocess(
            f"{shlex.quote(args.latex)} -recorder -interaction=errorstopmode -draftmode {stem}",
            workdir=workdir,
            check=False,
        )
        if cp.returncode != 0:
            path_log = Path(f"{path_stem}.log")
            error_info = parse_latex_log(path_log)
            error_info.print(path_log)
            sys.exit(1)

        aux_digest_hist.append(compute_file_digest(path_aux))

        cp = run_subprocess(f"{shlex.quote(args.bibtex)} {stem}", workdir=workdir, check=False)
        if cp.returncode != 0:
            path_blg = Path(f"{path_stem}.blg")
            error_info = parse_bibtex_log(path_blg)
            error_info.print(path_blg)
            sys.exit(1)
    else:
        amend(inp=[*inp, path_bbl], out=out, vol=vol)
        inventory_files = [*inp, path_bbl, *out]

    # Keep running LaTeX until the .aux file converges.
    for _ in range(args.maxrep):
        cp = run_subprocess(
            f"{shlex.quote(args.latex)} -recorder -interaction=errorstopmode {stem}",
            workdir=workdir,
            check=False,
        )
        path_log = Path(f"{path_stem}.log")
        error_info = parse_latex_log(path_log)
        if cp.returncode != 0:
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

    inventory_files.extend([f"{path_stem}.tex", path_aux, f"{path_stem}.pdf"])
    if args.inventory is not None:
        write_inventory(args.inventory, inventory_files, do_amend=False)

    # Look for input files and output files from the fls file.
    # These are usually worth tracking, but are not needed for the inventory file.
    # Relative paths in the fls file are relative to `workdir`.
    fls_inp = set()
    fls_vol = set()
    with open(f"{path_stem}.fls") as fh:
        for line in fh:
            if line.startswith("INPUT "):
                path = (workdir / line[6:].strip()).normpath()
                if not (path in inventory_files or path == args.inventory):
                    fls_inp.add(path)
            elif line.startswith("OUTPUT "):
                path = (workdir / line[7:].strip()).normpath()
                if not (path in inventory_files or path == args.inventory):
                    fls_vol.add(path)
    fls_inp.difference_update(fls_vol)
    # Both inputs and outputs must be filtered
    # because, strangely, LaTeX sometimes outputs files in the weirdest places,
    # e.g. in the TEXMF tree.
    amend(inp=filter_dependencies(fls_inp), vol=filter_dependencies(fls_vol))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-compile-latex",
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
    sys.exit(main())
