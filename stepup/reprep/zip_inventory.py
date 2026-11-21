# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Create ZIP with all files listed in an inventory file."""

import argparse
import datetime as dt
import stat
import sys
import tempfile
import zipfile
from collections.abc import Sequence

from stepup.core.path import Path, StrPath

from .inventory import LinkRecord, check_record, compute_record, open_inventory

__all__ = ("main", "zip_inventory")


TIMESTAMP = dt.datetime(1980, 1, 1).timestamp()

LINK_MODE = stat.S_IFLNK | 0o777
"""The mode stored in the ZIP file for every symbolic link, whatever its mode on disk.

Linux always gives a link these permission bits,
macOS derives them from the umask and Windows from the read-only attribute.
None of them uses the permission bits of a link for access checks,
so storing one fixed mode makes the ZIP file independent of the platform.
"""


def main(argv: Sequence[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="srr-zip-inventory", description="Create a reproducible ZIP file."
    )
    parser.add_argument(
        "inventory",
        help="The inventory file with all files to be zipped, with suffix .jsonl. "
        "The files will be checked against the inventory before archiving. "
        "The inventory file itself is not included in the ZIP.",
    )
    parser.add_argument("output_zip", nargs="?", help="Destination zip file.")
    args = parser.parse_args(argv)
    zip_inventory(args.inventory, args.output_zip)


def zip_inventory(path_inventory: StrPath, path_zip: StrPath | None = None):
    """Create a reproducible zip file.

    Parameters
    ----------
    path_inventory
        The inventory file, with suffix `.jsonl`.
        All files listed in the inventory are checked and then zipped.
        The paths in the ZIP file are those of the records,
        so they must not start with `../`.
        The inventory itself is not included in the ZIP file.
    path_zip
        The ZIP file to be created.
        When not given, the `.zip` suffix is added to the prefix of `path_inventory`.
        The existing ZIP file with the same path is only overwritten
        when the ZIP file is first succesfully created in a temporary directory.

    Raises
    ------
    ValueError
        When a file differs from its record,
        or when a record has a path outside the directory of the inventory.
    """
    path_inventory = Path(path_inventory)
    if not path_inventory.endswith(".jsonl"):
        raise ValueError(f"The inventory file must have a `.jsonl` extension. Got {path_inventory}")
    path_zip = Path(path_inventory[:-6] + ".zip" if path_zip is None else path_zip)
    if not path_zip.endswith(".zip"):
        raise ValueError(f"Destination must have a `.zip` extension. Got {path_zip}")

    root = path_inventory.parent
    with (
        tempfile.TemporaryDirectory("srr-zip-inventory") as path_tmp,
        open_inventory(path_inventory) as reader,
    ):
        header = reader.header
        path_tmp = Path(path_tmp)
        path_zip_tmp = path_tmp / "out.zip"
        with zipfile.ZipFile(path_zip_tmp, "w") as fz:
            for ref in reader:
                if ref.path == ".." or ref.path.startswith("../"):
                    raise ValueError(
                        f"Cannot zip {ref.path} from {path_inventory}, "
                        "because it is outside the directory of the inventory."
                    )
                # Copy the file to a temp dir.
                # This saves bandwith in case of remote datasets
                # and allows fixing the timestamp before compression.
                src = root / ref.path
                dst = path_tmp / "todo"
                dst.remove_p()
                src.copy(dst, follow_symlinks=False)
                new = compute_record(dst, path_tmp, header.hash_algorithm, header.mode)
                check_record(new, ref)
                if isinstance(ref, LinkRecord):
                    zipinfo = zipfile.ZipInfo(ref.path)
                    zipinfo.create_system = 3  # 3 means Unix
                    zipinfo.external_attr |= LINK_MODE << 16
                    fz.writestr(zipinfo, dst.readlink())
                else:
                    dst.utime((TIMESTAMP, TIMESTAMP))
                    fz.write(dst, ref.path, zipfile.ZIP_DEFLATED)
        path_zip_tmp.move(path_zip)


if __name__ == "__main__":
    sys.exit(main())
