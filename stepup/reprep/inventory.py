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
"""Inventory utilities."""

import stat

import attrs
from path import Path

from stepup.core.hash import compute_file_digest


@attrs.define
class FileSummary:
    """Data structure for a record in an inventory text file.

    There are a few different ways in which files are summarized:

    - Directories are never included.
    - The properties of ordinary files are just computed.
      The digest is a 64-bit BLAKE2B hash.
    - Symbolic links are not followed.
      Their size is None and the digest is derived from the link destination path,
      not the file contents.
      Links to directories are supported.
    """

    size: int | None = attrs.field()
    mode: str = attrs.field()
    digest: bytes = attrs.field()
    path: str = attrs.field()


def get_summary(path: str, root: str) -> FileSummary:
    """Compute a file summary for an inventory file.

    Parameters
    ----------
    path
        The location of the file to be summarized,
        relative to the current working directory.
    root
        The parent of the inventory file, to construct relative paths.

    Returns
    -------
    file_summary
        Contains the size, mode, digest, and relative path of the file.
    """
    path = Path(path)
    st = path.stat(follow_symlinks=False)
    size = None if stat.S_ISLNK(st.st_mode) else st.st_size
    mode = stat.filemode(st.st_mode)
    digest = compute_file_digest(path, follow_symlinks=False)
    relpath = path.relpath(root).normpath()
    return FileSummary(size, mode, digest, relpath)


def format_summary(fs: FileSummary) -> str:
    """Create a single-line string representation of the summary."""
    size_str = "               " if fs.size is None else format(fs.size, "15d")
    return f"{size_str} {fs.mode} {fs.digest.hex()} {fs.path}"


def parse_summary(line: str) -> FileSummary:
    """Convert a single-line string back into a summary."""
    if len(line) < 157:
        raise ValueError(f"Line too short to be converted to a FileSummary: {line}.")
    size_str = line[:15]
    size = None if size_str == "               " else int(size_str)
    mode = line[16:26]
    digest = bytes.fromhex(line[27:155])
    path = line[156:].strip()
    return FileSummary(size, mode, digest, path)


def check_summary(new: FileSummary, ref: FileSummary):
    """Verify that the new digest is consistent with the reference."""
    if new.size != ref.size:
        raise ValueError(f"File size should be {ref.size} but got {new.size}: {new.path}")
    if new.mode != ref.mode:
        raise ValueError(f"File mode should be {ref.mode} but got {new.mode}: {new.path}")
    if new.digest != ref.digest:
        raise ValueError(f"File digest mismatch: {new.path}")
