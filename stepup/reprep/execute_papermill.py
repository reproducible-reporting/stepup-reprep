# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Execution of notebooks with papermill.

The execution is implemented as a function here
instead of calling a `jupyter nbconvert` command directly,
to avoid creating a subprocess.
Performing the execution in the worker process is more efficient,
especially when executing many notebooks that all require the same imports.
"""

import argparse
import json
import sys
from collections.abc import Sequence

from papermill import execute_notebook
from path import Path

from stepup.reprep.jupyter_kernel import ipc_kernel_config

__all__ = ("main",)


def main(argv: Sequence[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if not args.path_inp.endswith(".ipynb"):
        raise ValueError("The input must have a .ipynb extension.")
    if not args.path_out.endswith(".ipynb"):
        raise ValueError("The output must have a .ipynb extension.")
    with ipc_kernel_config() as config:
        execute_notebook(
            input_path=args.path_inp,
            output_path=args.path_out,
            parameters=json.loads(args.parameters) if args.parameters else {},
            progress_bar=False,
            extra_arguments=["--IPKernelApp.log_level=40"],
            config=config,
        )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-execute-papermill", description="Execute a Jupyter notebook with papermill."
    )
    parser.add_argument(
        "path_inp", help="Path of the Jupyter notebook to execute and convert.", type=Path
    )
    parser.add_argument(
        "parameters", nargs="?", help="JSON serialized parameters for the notebook.", type=str
    )
    parser.add_argument("path_out", help="Path to the output notebook.", type=Path)
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
