# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Raster all pages in a PDF.

This is mainly intended to impede (the quality of) unauthorized copies.
"""

import argparse
from collections.abc import Sequence

import pymupdf

from stepup.core.api import getenv

__all__ = ("main", "raster_pdf")


def main(argv: Sequence[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if args.resolution is None:
        args.resolution = int(getenv("REPREP_RASTER_RESOLUTION", "100"))
    if args.quality is None:
        args.quality = int(getenv("REPREP_RASTER_QUALITY", "50"))

    raster_pdf(args.path_inp, args.path_out, args.resolution, args.quality)
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(prog="srr-raster-pdf", description="Raster a PDF file.")
    parser.add_argument("path_inp", help="The input PDF file.")
    parser.add_argument("path_out", help="The output PDF file.")
    parser.add_argument("-r", "--resolution", type=int, help="Bitmap resolution")
    parser.add_argument("-q", "--quality", type=int, help="JPEG quality")
    return parser.parse_args(argv)


def raster_pdf(path_inp: str, path_out: str, resolution: int, quality: int):
    """Convert a PDF into a rasterized version."""
    if not path_inp.endswith(".pdf"):
        raise ValueError(f"The input must have a `.pdf` extension, got: {path_inp}")
    if not path_out.endswith(".pdf"):
        raise ValueError(f"The output must have a `.pdf` extension, got: {path_out}")
    if resolution <= 0:
        raise ValueError(f"The resolution must be strictly positive, git: {resolution}")
    with pymupdf.open(path_inp) as src:
        dst = pymupdf.open()
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
        dst.save(path_out, garbage=4, deflate=True, no_new_id=True)


if __name__ == "__main__":
    main()
