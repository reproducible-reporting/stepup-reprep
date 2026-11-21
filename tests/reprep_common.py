# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Utilities shared by several unit test modules."""

import contextlib
import os
import tempfile

import pytest


@contextlib.contextmanager
def local_file(contents, filename, tmpdir):
    """Change to a temporary directory and create a file with given contents."""
    with contextlib.chdir(tmpdir):
        with open(filename, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(contents)
        yield


def symlinks_available() -> bool:
    """Whether this user can create symbolic links, which takes a privilege on Windows."""
    with tempfile.TemporaryDirectory() as path:
        try:
            os.symlink("target", os.path.join(path, "link"))
        except (OSError, NotImplementedError):
            return False
    return True


needs_symlinks = pytest.mark.skipif(not symlinks_available(), reason="Cannot create symbolic links")
