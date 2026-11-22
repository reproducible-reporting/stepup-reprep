# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Workarounds for `argparse` bugs in the oldest supported Python versions."""

import argparse
from collections.abc import Sequence

__all__ = ("parse_passthrough_args",)


def parse_passthrough_args(
    parser: argparse.ArgumentParser, argv: Sequence[str] | None = None
) -> argparse.Namespace:
    """Parse the arguments of a wrapper that passes the arguments after `--` to a wrapped tool.

    Parameters
    ----------
    parser
        A parser whose last positional argument has `nargs="*"`
        and collects the arguments for the wrapped tool.
    argv
        The command-line arguments, defaulting to `sys.argv[1:]`.

    Returns
    -------
    args
        The parsed arguments.
    """
    # Observed on Python 3.11.18 and 3.12.0 to 3.12.6 (fixed in 3.12.7):
    # `parse_args()` fills a trailing `nargs="*"` positional with an empty list too early
    # when it comes after another positional and an option.
    # The arguments after `--` are then rejected as unrecognized,
    # e.g. in `prog in.svg out.pdf --opt=x -- -T`.
    # `parse_intermixed_args()` handles such command lines correctly on all these versions.
    # Once `requires-python` is at least 3.12.7,
    # this module can be removed and its callers can use `parser.parse_args()` again.
    return parser.parse_intermixed_args(argv)
