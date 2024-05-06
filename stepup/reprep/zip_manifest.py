# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# Copyright (C) 2024 Toon Verstraelen
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
"""Create ZIP with all files listed in a MANIFEST.txt file."""

import argparse
import datetime
import sys
import tempfile
import zipfile

from path import Path

from stepup.core.hash import compute_file_digest

from .check_manifest import iter_manifest

__all__ = ("zip_manifest",)


TIMESTAMP = datetime.datetime(1980, 1, 1).timestamp()


def main() -> int:
    """Main program."""
    args = parse_args()
    return zip_manifest(args.manifest_txt, args.output_zip)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-zip-manifest", description="Create a reproducible ZIP file."
    )
    parser.add_argument(
        "manifest_txt",
        help="The MANIFEST.txt with all files to be zipped. "
        "The digests of the files will be checked before archiving. "
        "The manifest file will be included in the ZIP.",
    )
    parser.add_argument("output_zip", help="Destination zip file.")
    return parser.parse_args()


def zip_manifest(path_manifest: str, path_zip: str, check: bool = True) -> int:
    """Create a reproducible zip file.

    Parameters
    ----------
    path_manifest
        The MANIFEST.txt file
    path_zip
        The ZIP file to be created.
    check
        When True, the file will be validated with size and hash
        before adding it to the ZIP file.
        In case of a mismatch, the partial ZIP is removed.
    """
    if not path_zip.endswith(".zip"):
        print(f"Destination must have a `.zip` extension. Got {path_zip}", file=sys.stderr)
        return 2
    path_zip = Path(path_zip)
    if not path_manifest.endswith(".txt"):
        print(
            f"Manifest file must have a `.sha256` extension. Got {path_manifest}", file=sys.stderr
        )
        return 2
    path_manifest = Path(path_manifest)

    # Create new one.
    root = path_manifest.parent
    nskip = 0 if root == "" else len(root) + 1
    result = 0
    with tempfile.TemporaryDirectory("reprep-zip-manifest") as tmpdir:
        tmpdir = Path(tmpdir)
        path_zip_tmp = tmpdir / "out.zip"
        with zipfile.ZipFile(path_zip_tmp, "w") as fz:
            for size, digest, src in iter_manifest(path_manifest):
                # Copy the file to a temp dir.
                # This saves bandwith in case of remote datasets and allows
                # fixing the timestamp before compression.
                dst = tmpdir / "todo"
                src.copy(dst)
                dst.utime((TIMESTAMP, TIMESTAMP))
                # Check if needed
                if check:
                    actual_size = Path(dst).getsize()
                    if size != actual_size:
                        print(
                            f"Size {actual_size} of {src} differs from expected size {size}",
                            file=sys.stderr,
                        )
                        result = 2
                        break
                    actual_digest = compute_file_digest(src)
                    if digest != actual_digest:
                        print(f"Digest mismatch for file: {src}", file=sys.stderr)
                        result = 3
                        break
                # Compress
                fz.write(dst, src[nskip:], zipfile.ZIP_DEFLATED)
            dst = tmpdir / "todo"
            path_manifest.copy(dst)
            dst.utime((TIMESTAMP, TIMESTAMP))
            fz.write(dst, path_manifest[nskip:], zipfile.ZIP_DEFLATED)

        if result == 0:
            path_zip_tmp.move(path_zip)
    return result


if __name__ == "__main__":
    sys.exit(main())
