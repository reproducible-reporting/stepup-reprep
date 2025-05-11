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
"""Create ZIP with all files listed in an inventory.txt file."""

import argparse
import datetime
import sys
import tempfile
import zipfile

from path import Path

from .check_inventory import iter_inventory
from .inventory import check_summary, get_summary

__all__ = ("zip_inventory",)


TIMESTAMP = datetime.datetime(1980, 1, 1).timestamp()


def main(argv: list[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="rr-zip-inventory", description="Create a reproducible ZIP file."
    )
    add_parser_args(parser)
    args = parser.parse_args(argv)
    zip_inventory(args.inventory_txt, args.output_zip)


def add_parser_args(parser: argparse.ArgumentParser):
    """Define command-line arguments."""
    parser.add_argument(
        "inventory_txt",
        help="The inventory file with all files to be zipped. "
        "The digests of the files will be checked before archiving. "
        "The inventory file will be included in the ZIP.",
    )
    parser.add_argument("output_zip", nargs="?", help="Destination zip file.")


def zip_subcommand(subparser: argparse.ArgumentParser) -> callable:
    parser = subparser.add_parser(
        "zip-inventory",
        help="Create a reproducible ZIP file.",
    )
    add_parser_args(parser)
    return zip_tool


def zip_tool(args: argparse.Namespace) -> int:
    """Create a reproducible ZIP file."""
    zip_inventory(args.inventory_txt, args.output_zip)
    return 0


def zip_inventory(path_inventory: str, path_zip: str | None = None):
    """Create a reproducible zip file.

    Parameters
    ----------
    path_inventory
        The inventory.txt file.
        All files listed in the inventory are checked and then zipped.
    path_zip
        The ZIP file to be created.
        When not given, the `.zip` suffix is added to the prefix of `path_inventory`.
        The existing ZIP file with the same path is only overwritten when the ZIP
        file is first succesfully created in a temporary directory.
    """
    if not path_inventory.endswith(".txt"):
        raise ValueError(f"The inventory file must have a `.txt` extension. Got {path_inventory}")
    path_inventory = Path(path_inventory)
    if path_zip is None:
        path_zip = path_inventory[:-4] + ".zip"
    elif not path_zip.endswith(".zip"):
        raise ValueError(f"Destination must have a `.zip` extension. Got {path_zip}")
    path_zip = Path(path_zip)

    # Create a new ZIP archive.
    root = path_inventory.parent
    nskip = 0 if root == "" else len(root) + 1
    with tempfile.TemporaryDirectory("rr-zip-inventory") as path_tmp:
        path_tmp = Path(path_tmp)
        path_zip_tmp = path_tmp / "out.zip"
        with zipfile.ZipFile(path_zip_tmp, "w") as fz:
            for ref in iter_inventory(path_inventory):
                # Copy the file to a temp dir.
                # This saves bandwith in case of remote datasets and allows
                # fixing the timestamp before compression.
                src = Path(root / ref.path)
                dst = path_tmp / "todo"
                dst.remove_p()
                src.copy(dst, follow_symlinks=False)
                # Check the file before adding it to the ZIP
                new = get_summary(dst, path_tmp)
                check_summary(new, ref)
                # Store
                if ref.size is None:
                    # Symbolic link
                    zipinfo = zipfile.ZipInfo(src[nskip:])
                    zipinfo.create_system = 3  # 3 means Unix
                    zipinfo.external_attr |= dst.stat(follow_symlinks=False).st_mode << 16
                    fz.writestr(zipinfo, dst.readlink())
                else:
                    # Actual file
                    dst.utime((TIMESTAMP, TIMESTAMP))
                    fz.write(dst, src[nskip:], zipfile.ZIP_DEFLATED)
            dst = path_tmp / "todo"
            path_inventory.copy(dst)
            dst.utime((TIMESTAMP, TIMESTAMP))
            fz.write(dst, path_inventory[nskip:], zipfile.ZIP_DEFLATED)
        path_zip_tmp.move(path_zip)


if __name__ == "__main__":
    main(sys.argv[1:])
