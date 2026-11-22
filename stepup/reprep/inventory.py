# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Format of inventory files, with the computation, comparison and reading of their records.

An inventory is a JSON Lines file, see `docs/advanced_topics/inventory_files.md`.
The first line is a header and every other line is the record of one file.
"""

import contextlib
import hashlib
import json
import os
import re
import stat
from collections.abc import Iterator
from pathlib import PureWindowsPath
from typing import Any, BinaryIO

import attrs

from stepup.core.path import Path, StrPath
from stepup.core.platform.oscompat import file_modes_available
from stepup.core.utils import open_regular_file

__all__ = (
    "HASH_ALGORITHMS",
    "FileRecord",
    "InventoryHeader",
    "InventoryReader",
    "LinkRecord",
    "check_record",
    "compute_record",
    "format_header",
    "format_record",
    "open_inventory",
)


INVENTORY_FORMAT = "stepup-inventory"
"""The value of the `format` key in the header, which tells an inventory apart from other files."""

INVENTORY_VERSION = 1
"""The value of the `version` key in the header,
which changes with every incompatible change of the format."""

HEADER_KEYS = frozenset(["fields", "format", "version"])
"""The keys of the header on the first line of an inventory."""

LINK_KEYS = frozenset(["link", "path"])
"""The keys of the record of a symbolic link."""

HASH_ALGORITHMS = tuple(
    sorted(name for name in hashlib.algorithms_guaranteed if not name.startswith("shake_"))
)
"""The hash algorithms that can digest the regular files in an inventory.

The `shake_*` algorithms are left out, because their digests have no fixed length.
"""

MAX_LINE_LENGTH = 65536
"""The length in bytes of the longest line that is read from an inventory.

A record is much shorter, so a longer line means that the file is not an inventory,
e.g. a data file given where the inventory belongs, which is then rejected without loading it.
"""

MODE_PATTERN = re.compile("[r-][w-][xsS-][r-][w-][xsS-][r-][w-][xtT-]")
"""The permission bits of a file, as formatted by `stat.filemode` without the file type."""


@attrs.define(frozen=True)
class InventoryHeader:
    """The properties of an inventory that apply to all of its records."""

    hash_algorithm: str = attrs.field(validator=attrs.validators.in_(HASH_ALGORITHMS))
    """The name of the `hashlib` algorithm that digests the regular files."""

    mode: bool = attrs.field(default=False)
    """Whether the permission bits of the regular files are recorded."""

    @property
    def fields(self) -> list[str]:
        """The sorted keys of the record of a regular file."""
        fields = ["path", "size", self.hash_algorithm]
        if self.mode:
            fields.append("mode")
        return sorted(fields)


@attrs.define(frozen=True)
class FileRecord:
    """The record of a regular file in an inventory."""

    path: str = attrs.field()
    """The file, relative to the parent of the inventory, with `/` separators."""

    digest: str = attrs.field()
    """The digest of the file contents, in lowercase hexadecimal digits."""

    size: int = attrs.field()
    """The size of the file in bytes."""

    mode: str | None = attrs.field(default=None)
    """The permission bits of the file, e.g. `rw-r--r--`, or `None` when they are not recorded."""


@attrs.define(frozen=True)
class LinkRecord:
    """The record of a symbolic link in an inventory.

    The link is not followed, so the record only describes the link itself.
    """

    path: str = attrs.field()
    """The link, relative to the parent of the inventory, with `/` separators."""

    target: str = attrs.field()
    """The target as stored in the link."""


Record = FileRecord | LinkRecord


def compute_record(
    path: StrPath, root: StrPath, hash_algorithm: str = "md5", mode: bool = False
) -> Record:
    """Compute the record of a file for an inventory.

    Parameters
    ----------
    path
        The file to describe, relative to the current working directory.
        A symbolic link is described as a link and is never followed.
    root
        The parent of the inventory, to which the path in the record is relative.
    hash_algorithm
        The name of the `hashlib` algorithm that digests a regular file.
    mode
        Whether to record the permission bits of a regular file.

    Returns
    -------
    record
        The record of the regular file or of the symbolic link.

    Raises
    ------
    NotARegularFileError
        When the file is neither a regular file nor a symbolic link, e.g. a directory or a FIFO.
    """
    path = Path(path)
    relpath = str(path.relpath(root).normpath())
    reason = _check_record_path(relpath)
    if reason is not None:
        raise ValueError(f"Cannot write {path} in an inventory, because its path {reason}.")
    if stat.S_ISLNK(path.stat(follow_symlinks=False).st_mode):
        return LinkRecord(relpath, str(path.readlink()))
    with open(path, "rb", opener=open_regular_file) as fh:
        st = os.fstat(fh.fileno())
        digest = hashlib.file_digest(fh, hash_algorithm).hexdigest()
    return FileRecord(relpath, digest, st.st_size, stat.filemode(st.st_mode)[1:] if mode else None)


def check_record(new: Record, ref: Record):
    """Verify that a newly computed record is consistent with the reference.

    The paths of the two records are not compared.
    The permission bits are only compared when the reference has them
    and when files have permission bits on this platform,
    see `file_modes_available()` in `stepup.core.platform.oscompat`.

    Raises
    ------
    TypeError
        When one is a symbolic link and the other is not.
    ValueError
        When the size, the digest, the permission bits or the link target differ.
    """
    if isinstance(ref, LinkRecord):
        if not isinstance(new, LinkRecord):
            raise TypeError(f"Expected a symbolic link but got a regular file: {ref.path}")
        if new.target != ref.target:
            raise ValueError(f"Link target should be {ref.target} but got {new.target}: {ref.path}")
        return
    if not isinstance(new, FileRecord):
        raise TypeError(f"Expected a regular file but got a symbolic link: {ref.path}")
    if new.size != ref.size:
        raise ValueError(f"File size should be {ref.size} but got {new.size}: {ref.path}")
    if ref.mode is not None and file_modes_available() and new.mode != ref.mode:
        raise ValueError(f"File mode should be {ref.mode} but got {new.mode}: {ref.path}")
    if new.digest != ref.digest:
        raise ValueError(f"File digest mismatch: {ref.path}")


def _dump_line(data: dict[str, Any]) -> str:
    """Format one line of an inventory, without the trailing newline."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def format_header(header: InventoryHeader) -> str:
    """Format the first line of an inventory, without the trailing newline."""
    return _dump_line(
        {"fields": header.fields, "format": INVENTORY_FORMAT, "version": INVENTORY_VERSION}
    )


def format_record(record: Record, header: InventoryHeader) -> str:
    """Format the line of one record in an inventory, without the trailing newline.

    Raises
    ------
    ValueError
        When the presence of the permission bits in a file record does not match the header.
    """
    if isinstance(record, LinkRecord):
        return _dump_line({"link": record.target, "path": record.path})
    if (record.mode is not None) != header.mode:
        raise ValueError(f"The permission bits do not match the inventory header: {record.path}")
    data = {"path": record.path, "size": record.size, header.hash_algorithm: record.digest}
    if header.mode:
        data["mode"] = record.mode
    return _dump_line(data)


@attrs.define
class InventoryReader:
    """Iterate over the records of an open inventory, validating each one.

    Create it with `open_inventory()`, which reads and validates the header first.
    """

    path: Path = attrs.field()
    """The inventory file, used in the messages."""

    header: InventoryHeader = attrs.field()
    """The header on the first line of the inventory."""

    _fh: BinaryIO = attrs.field()
    """The inventory file, open in binary mode, of which the header has been read."""

    def __iter__(self) -> Iterator[Record]:
        """Read and validate the remaining lines, one record at a time.

        Raises
        ------
        ValueError
            When a line is not a valid record, or when two records have the same path.
        """
        seen = set()
        iline = 2
        while True:
            data = _read_line(self.path, self._fh, iline)
            if data is None:
                return
            record = _load_record(self.path, self.header, iline, data)
            if record.path in seen:
                raise _not_an_inventory(self.path, f"line {iline} repeats the path {record.path!r}")
            seen.add(record.path)
            yield record
            iline += 1


@contextlib.contextmanager
def open_inventory(path_inventory: StrPath) -> Iterator[InventoryReader]:
    """Open an inventory and validate its header.

    The records are read one line at a time while iterating over the reader,
    so an inventory is never loaded as a whole.

    Parameters
    ----------
    path_inventory
        The inventory to read.

    Returns
    -------
    reader
        The reader, of which `header` is the validated header
        and which yields the records when iterating over it.

    Raises
    ------
    ValueError
        When the file does not exist or when it is not an inventory in a supported version.
        The message is the complete diagnosis.

    Examples
    --------
    ```python
    with open_inventory("inventory.jsonl") as reader:
        for record in reader:
            print(record.path)
    ```
    """
    path_inventory = Path(path_inventory)
    if not path_inventory.is_file():
        raise ValueError(
            f"The inventory {path_inventory} does not exist. Write it with `srr-make-inventory`."
        )
    with open(path_inventory, "rb") as fh:
        data = _read_line(path_inventory, fh, 1)
        if data is None:
            raise _not_an_inventory(path_inventory, "it is empty")
        yield InventoryReader(path_inventory, _load_header(path_inventory, data), fh)


def _read_line(path_inventory: Path, fh: BinaryIO, iline: int) -> Any:
    """Read the next line of an inventory as JSON.

    Every line is decoded on its own,
    so that invalid UTF-8 is reported on the line where it occurs.

    Parameters
    ----------
    path_inventory
        The inventory file, used in the messages.
    fh
        The inventory file, open in binary mode.
    iline
        The 1-based number of the line to read, used in the messages.

    Returns
    -------
    data
        The JSON data on the line, or `None` at the end of the file.
    """
    line = fh.readline(MAX_LINE_LENGTH)
    if line == b"":
        return None
    if not line.endswith(b"\n"):
        if len(line) == MAX_LINE_LENGTH:
            reason = f"line {iline} is longer than {MAX_LINE_LENGTH} bytes"
        else:
            reason = f"line {iline} does not end with a newline"
        raise _not_an_inventory(path_inventory, reason)
    try:
        text = line.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _not_an_inventory(path_inventory, f"line {iline} is not valid UTF-8") from exc
    try:
        return json.loads(text)
    except ValueError as exc:
        raise _not_an_inventory(path_inventory, f"line {iline} is not valid JSON") from exc


def _load_header(path_inventory: Path, data: Any) -> InventoryHeader:
    """Validate the header on the first line of an inventory.

    Parameters
    ----------
    path_inventory
        The inventory file, used in the messages.
    data
        The JSON data on the first line.

    Returns
    -------
    header
        The validated header.
    """
    if not isinstance(data, dict) or data.get("format") != INVENTORY_FORMAT:
        raise _not_an_inventory(
            path_inventory, f"line 1 is not a JSON object with format {INVENTORY_FORMAT!r}"
        )
    version = data.get("version")
    if type(version) is not int or version != INVENTORY_VERSION:
        raise ValueError(
            f"The inventory {path_inventory} has version {version!r}, "
            f"while this version of StepUp RepRep reads version {INVENTORY_VERSION!r}. "
            "Write it again with `srr-make-inventory`."
        )
    if data.keys() != HEADER_KEYS:
        raise _not_an_inventory(
            path_inventory, f"the keys on line 1 are not {', '.join(sorted(HEADER_KEYS))}"
        )
    fields = data["fields"]
    if not (isinstance(fields, list) and all(isinstance(field, str) for field in fields)):
        raise _not_an_inventory(path_inventory, "the fields on line 1 are not a list of strings")
    algorithms = [field for field in fields if field not in ("mode", "path", "size")]
    if len(algorithms) != 1 or algorithms[0] not in HASH_ALGORITHMS:
        raise _not_an_inventory(
            path_inventory,
            "the fields on line 1 do not have exactly one hash algorithm "
            f"out of {', '.join(HASH_ALGORITHMS)}",
        )
    header = InventoryHeader(algorithms[0], "mode" in fields)
    if fields != header.fields:
        raise _not_an_inventory(
            path_inventory,
            f"the fields on line 1 are not the sorted list {', '.join(header.fields)}",
        )
    return header


def _load_record(path_inventory: Path, header: InventoryHeader, iline: int, data: Any) -> Record:
    """Validate the record of one file in an inventory.

    Parameters
    ----------
    path_inventory
        The inventory file, used in the messages.
    header
        The header of the inventory, which defines the keys of a regular file record.
    iline
        The 1-based number of the line, used in the messages.
    data
        The JSON data on the line.

    Returns
    -------
    record
        The validated record.
    """
    where = f"line {iline}"
    if isinstance(data, dict) and "link" in data:
        if data.keys() != LINK_KEYS:
            keys = ", ".join(sorted(LINK_KEYS))
            raise _not_an_inventory(
                path_inventory, f"{where} is a link without exactly the keys {keys}"
            )
        target = data["link"]
        if not (isinstance(target, str) and len(target) > 0):
            raise _not_an_inventory(
                path_inventory, f"the link target on {where} is not a non-empty string"
            )
        return LinkRecord(_load_record_path(path_inventory, where, data["path"]), target)
    if not isinstance(data, dict) or data.keys() != set(header.fields):
        raise _not_an_inventory(
            path_inventory,
            f"{where} is not a JSON object with the keys {', '.join(header.fields)}",
        )
    path = _load_record_path(path_inventory, where, data["path"])
    size = data["size"]
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise _not_an_inventory(path_inventory, f"the size on {where} is not a non-negative int")
    digest = data[header.hash_algorithm]
    num_digits = 2 * hashlib.new(header.hash_algorithm).digest_size
    if not (isinstance(digest, str) and re.fullmatch(f"[0-9a-f]{{{num_digits}}}", digest)):
        raise _not_an_inventory(
            path_inventory,
            f"the {header.hash_algorithm} digest on {where} "
            f"does not have {num_digits} lowercase hexadecimal digits",
        )
    mode = data.get("mode")
    if header.mode and not (isinstance(mode, str) and MODE_PATTERN.fullmatch(mode)):
        raise _not_an_inventory(
            path_inventory, f"the mode on {where} does not have the form rw-r--r--"
        )
    return FileRecord(path, digest, size, mode)


def _load_record_path(path_inventory: Path, where: str, path: Any) -> str:
    """Validate the path of a record, see `_check_record_path`."""
    reason = _check_record_path(path)
    if reason is not None:
        raise _not_an_inventory(path_inventory, f"the path on {where} {reason}")
    return path


def _check_record_path(path: Any) -> str | None:
    """Check that a path can be written in an inventory.

    A valid path is a non-empty string that is relative, normalized,
    uses `/` as separator and does not name a directory.
    It may start with `../`.

    Parameters
    ----------
    path
        The path in the record of a file.

    Returns
    -------
    reason
        `None` for a valid path, otherwise why it is invalid,
        phrased to complete a sentence that starts with the path.
    """
    if not (isinstance(path, str) and len(path) > 0):
        return "is not a non-empty string"
    if "\\" in path:
        return f"contains a backslash: {path}"
    if path.startswith("/") or PureWindowsPath(path).is_absolute():
        return f"is absolute: {path}"
    if Path(path).normpath() != path or Path(path).name in (".", ".."):
        return f"is not the normalized path of a file: {path}"
    return None


def _not_an_inventory(path_inventory: Path, reason: str) -> ValueError:
    """Create the error for a file that is not an inventory in the current format.

    The message does not suggest writing the inventory to the same path,
    because the file may well be a data file that was given where the inventory belongs.
    """
    return ValueError(
        f"The file {path_inventory} is not an inventory written by `srr-make-inventory`, "
        f"because {reason}."
    )
