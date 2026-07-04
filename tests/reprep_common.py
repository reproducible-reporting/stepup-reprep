# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Utilities shared by several unit test modules."""

import contextlib


@contextlib.contextmanager
def local_file(contents, filename, tmpdir):
    """Change to a temporary directory and create a file with given contents."""
    with contextlib.chdir(tmpdir):
        with open(filename, "w") as fh:
            fh.write(contents)
        yield
