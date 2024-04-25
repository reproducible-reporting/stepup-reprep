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
r"""RepRep Wrapper for LaTeX."""

import argparse
import subprocess
import sys

from path import Path

from stepup.core.api import amend, getenv
from stepup.core.hash import compute_file_digest
from stepup.reprep.make_manifest import write_manifest

from .bibtex_log import parse_bibtex_log
from .latex_deps import scan_latex_deps
from .latex_log import ErrorInfo, parse_latex_log


def main() -> int:
    """Main program."""
    args = parse_args()

    workdir, fn_tex = Path(args.path_tex).splitpath()
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
    implicit, bib = scan_latex_deps(fn_tex)

    # Get LaTeX executable
    if args.latex is None:
        args.latex = getenv("REPREP_LATEX", "pdflatex")

    aux_digest_hist = []
    if len(bib) == 0:
        if not amend(inp=implicit):
            return 0
        manifest_files = list(implicit)
    elif args.run_bibtex:
        # Get other executables and files
        if args.bibtex is None:
            args.bibtex = getenv("REPREP_BIBTEX", "bibtex")
        if args.bibsane is None:
            args.bibsane = getenv("REPREP_BIBSANE", "bibsane")
        paths_config = []
        if args.bibsane_config is None:
            args.bibsane_config = getenv("REPREP_BIBSANE_CONFIG", "bibsane.yaml", is_path=True)
            paths_config.append(args.bibsane_config)

        if not amend(
            inp=implicit + bib + paths_config,
            out=[f"{stem}.bbl"],
        ):
            return 0
        manifest_files = [*implicit, *bib, f"{stem}.bbl"]

        # LaTeX
        cp = subprocess.run(
            [
                args.latex,
                "-interaction=errorstopmode",
                "-draftmode",
                stem,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            cwd=workdir,
        )
        if cp.returncode != 0:
            path_log = workdir / f"{stem}.log"
            error_info = parse_latex_log(path_log)
            error_info.print(path_log)
            return 1

        aux_digest_hist.append(compute_file_digest(path_aux))

        # BibTeX
        cp = subprocess.run(
            [args.bibtex, stem],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            cwd=workdir,
        )
        if cp.returncode != 0:
            path_blg = workdir / f"{stem}.blg"
            error_info = parse_bibtex_log(path_blg)
            error_info.print(path_blg)
            return 2

        # BibSane
        cp = subprocess.run(
            [args.bibsane, f"{stem}.aux", f"--config={args.bibsane_config}"],
            cwd=workdir,
            text=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if cp.returncode != 0:
            error_info = ErrorInfo("BibSane", src=f"{workdir}/{stem}.aux")
            error_info.print()
            sys.stdout.write(cp.stdout)
            return 3
    else:
        if not amend(inp=[*implicit, f"{stem}.bbl"]):
            return 0
        manifest_files = [*implicit, f"{stem}.bbl"]

    for _ in range(args.maxrep):
        # LaTeX
        cp = subprocess.run(
            [args.latex, "-interaction=errorstopmode", stem],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            cwd=workdir,
        )
        path_log = workdir / f"{stem}.log"
        error_info = parse_latex_log(path_log)
        if cp.returncode != 0:
            error_info.print(path_log)
            return 4
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
        return -3

    manifest_files.extend([f"{stem}.tex", f"{stem}.aux", f"{stem}.pdf"])
    path_manifest = f"{stem}.MANIFEST.txt"
    write_manifest(path_manifest, manifest_files)

    vol_paths = []
    for path in Path(".").glob(f"{stem}.*"):
        path = path.normpath()
        if not (path in manifest_files or path == path_manifest):
            vol_paths.append(path)
    amend(vol=vol_paths)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-latex",
        description="Compile a LaTeX document and print essence from log file.",
    )
    parser.add_argument("path_tex", help="The main LaTeX source file.")
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
        help="Run bibtex and bibsane.",
    )
    parser.add_argument(
        "--bibtex",
        help="The BibTeX executable. "
        "The default is ${REPREP_BIBTEX} or bibtex if the variable is not defined.",
    )
    parser.add_argument(
        "--bibsane",
        help="The BibSane executable. "
        "The default is ${REPREP_BIBSANE} or bibsane if the variable is not defined.",
    )
    parser.add_argument(
        "--bibsane-config",
        help="The BibSane configuration file. The default is ${REPREP_BIBSANE_CONFIG} or "
        "bibsane.yaml if the variables is not defined.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
