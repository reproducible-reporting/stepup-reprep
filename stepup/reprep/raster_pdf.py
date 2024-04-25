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
"""Raster all pages in a PDF.

This is mainly intended to impede (the quality of) unauthorized copies.
"""

import argparse
import os
import sys

import fitz

from stepup.core.api import amend

__all__ = ("raster_pdf",)


def main() -> int:
    """Main program."""
    args = parse_args()
    if args.resolution is None:
        amend(env=["REPREP_RASTER_RESOLUTION"])
        args.resolution = int(os.environ.get("REPREP_RASTER_RESOLUTION", "100"))
    if args.quality is None:
        amend(env=["REPREP_RASTER_QUALITY"])
        args.quality = int(os.environ.get("REPREP_RASTER_QUALITY", "50"))

    raster_pdf(args.path_inp, args.path_out, args.resolution, args.quality)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(prog="reprep-raster-pdf", description="Raster a PDF file.")
    parser.add_argument("path_inp", help="The input PDF file.")
    parser.add_argument("path_out", help="The output PDF file.")
    parser.add_argument("-r", "--resolution", type=int, help="Bitmap resolution")
    parser.add_argument("-q", "--quality", type=int, help="JPEG quality")
    return parser.parse_args()


def raster_pdf(path_inp: str, path_out: str, resolution: int, quality: int):
    """Convert a PDF into a rasterized version."""
    if not path_inp.endswith(".pdf"):
        print(f"The input must have a `.pdf` extension, got: {path_inp}", file=sys.stderr)
        return 2
    if not path_out.endswith(".pdf"):
        print(f"The output must have a `.pdf` extension, got: {path_out}", file=sys.stderr)
        return 2
    if resolution <= 0:
        print(f"The resolution must be strictly positive, git: {resolution}", file=sys.stderr)
    with fitz.open(path_inp) as src:
        dst = fitz.open()
        for src_page in src:
            src_page.wrap_contents()
            if src_page.rotation in (90, 270):
                height, width = src_page.mediabox_size
            else:
                width, height = src_page.mediabox_size
            pix = src_page.get_pixmap(dpi=resolution)
            stream = pix.tobytes(output="jpg", jpg_quality=quality)
            dst_page = dst.new_page(-1, width, height)
            dst_page.insert_image(dst_page.rect, stream=stream)
        dst.save(path_out, garbage=4, deflate=True, linear=True, no_new_id=True)


if __name__ == "__main__":
    sys.exit(main())
