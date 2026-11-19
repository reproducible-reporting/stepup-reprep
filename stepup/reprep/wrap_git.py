# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""RepRep Wrapper for git commands that take the current commit id as a dependency."""

import argparse
import shlex
import sys
from collections.abc import Sequence

from stepup.core.api import amend
from stepup.core.extapi import run_subprocess
from stepup.core.path import Path

__all__ = ("main",)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-wrap-git", description="Run git commands that depend on the current commit id."
    )
    parser.add_argument(
        "--stdout",
        type=Path,
        help="File to redirect the standard output of the command to. "
        "If not specified, the output will be printed to the console.",
    )
    parser.add_argument(
        "git_args",
        nargs="*",
        type=str,
        help="The git command to run.",
    )
    return parser.parse_args(argv)


def git_paths(*names: str) -> list[Path]:
    """Locate files in the git directory, as `git rev-parse --git-path` does.

    This takes worktrees and submodules into account,
    in which `.git` is a file and some files are found in a common git directory.

    Parameters
    ----------
    names
        Paths relative to the git directory, e.g. `HEAD` or `refs/heads/main`.

    Returns
    -------
    paths
        The corresponding paths, relative to the current directory unless git returns them absolute.
    """
    git_args = ["git", "rev-parse"]
    for name in names:
        git_args.extend(["--git-path", name])
    cp = run_subprocess(shlex.join(git_args), check=False)
    if cp.returncode != 0:
        raise RuntimeError(f"Failed to locate files in the git directory:\n{cp.stderr}")
    return [Path(line) for line in cp.stdout.splitlines()]


def amend_head_inputs() -> None:
    """Amend the step with the files in the git directory that determine the commit of HEAD.

    These are:

    - `HEAD` itself, which contains the commit id when HEAD is detached.
    - When HEAD is a symbolic reference, the loose ref file of the branch it points to.
    - When that branch has no loose ref file (e.g. after `git gc`),
      `packed-refs` and the reflog `logs/HEAD`, if present.
      The reflog is needed because a new commit creates a loose ref
      without changing `packed-refs`.

    Raises
    ------
    RuntimeError
        When HEAD points to a branch that has no loose ref file and there is no `packed-refs`.
        This happens on a branch without commits,
        and in repositories with the `reftable` ref storage format, which is not supported.
    """
    (path_head,) = git_paths("HEAD")
    amend(inp=path_head)
    with open(path_head, encoding="utf-8") as fh:
        head_content = fh.read().strip()
    if not head_content.startswith("ref: "):
        return
    ref = head_content.removeprefix("ref: ").strip()
    path_ref, path_packed, path_log = git_paths(ref, "packed-refs", "logs/HEAD")
    if path_ref.is_file():
        amend(inp=path_ref)
    elif path_packed.is_file():
        amend(inp=[path_packed, path_log] if path_log.is_file() else path_packed)
    else:
        raise RuntimeError(
            f"Cannot find {ref} in {path_ref} or {path_packed}. "
            "Either the branch has no commits yet, "
            "or the repository uses the reftable ref storage format, which is not supported."
        )


def main(argv: Sequence[str] | None = None) -> None:
    """Main program."""
    args = parse_args(argv)
    amend_head_inputs()
    command = "GIT_PAGER=cat " + shlex.join(args.git_args)
    cp = run_subprocess(command, check=False)
    if args.stdout is None:
        sys.stdout.write(cp.stdout)
    else:
        with open(args.stdout, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    if cp.returncode != 0:
        sys.exit(cp.returncode)


if __name__ == "__main__":
    sys.exit(main())
