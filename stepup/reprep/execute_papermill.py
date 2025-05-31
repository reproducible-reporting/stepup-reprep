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
"""Execution of notebooks with papermill.

The execution is implemented as a function here instead of calling
a `jupyter nbconvert` command directly, to avoid creating a subprocess.
Performing the execution in the worker process is more efficient,
especially when executing many notebooks that all require the same imports.
"""

import argparse
import json
import sys

from papermill import execute_notebook
from path import Path


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if not args.path_inp.endswith(".ipynb"):
        raise ValueError("The input must have a .ipynb extension.")
    if not args.path_out.endswith(".ipynb"):
        raise ValueError("The output must have a .ipynb extension.")
    execute_notebook(
        input_path=args.path_inp,
        output_path=args.path_out,
        parameters=json.loads(args.parameters) if args.parameters else {},
        progress_bar=False,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Define command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert a Jupyter notebook to HTML.")
    parser.add_argument(
        "path_inp", help="Path of the Jupyter notebook to execute and convert.", type=Path
    )
    parser.add_argument(
        "parameters", nargs="?", help="JSON serialized parameters for the notebook.", type=str
    )
    parser.add_argument("path_out", help="Path to the output notebook.", type=Path)
    return parser.parse_args(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
