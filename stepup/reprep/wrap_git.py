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
"""RepRep Wrapper for git commands that take the current commit id as a dependency."""

import argparse
import shlex
import sys

from path import Path

from stepup.core.api import amend
from stepup.core.utils import myrelpath
from stepup.core.worker import WorkThread


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="wrap_git", description="Run git commands that depend on the current commit id."
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output file to write the command to. "
        "If not specified, the command is printed to stdout.",
    )
    parser.add_argument(
        "git_args",
        nargs="*",
        type=str,
        help="The git command to run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, work_thread: WorkThread | None = None) -> None:
    """Main program."""
    args = parse_args(argv)
    if work_thread is None:
        work_thread = WorkThread("stub")

    # Determine the git root directory.
    return_code, git_root, _ = work_thread.runsh("git rev-parse --show-toplevel")
    if return_code != 0:
        raise RuntimeError("Failed to determine git root directory.")
    git_root = myrelpath(git_root.strip())

    # Mark the HEAD file as an input dependency.
    head_path = git_root / ".git" / "HEAD"
    amend(inp=head_path)
    with open(head_path) as fh:
        head_content = fh.read().strip()
        if not head_content.startswith("ref: "):
            raise ValueError("HEAD is not a symbolic reference, cannot determine commit id.")
    ref_path = head_content[5:].strip()

    # Mark the ref path as an input dependency.
    amend(inp=git_root / ".git" / ref_path)

    # Run the git command.
    command = "GIT_PAGER=cat " + shlex.join(args.git_args)
    if args.out is not None:
        command = f"{command} > {shlex.quote(args.out)}"
    work_thread.runsh_verbose(command)


if __name__ == "__main__":
    main(sys.argv[1:])
