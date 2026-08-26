# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Put multiple pages per sheet using a fixed layout."""

import argparse
from collections.abc import Sequence

import pymupdf

from stepup.core.api import getenv

__all__ = ("main", "nup_pdf")


def main(argv: Sequence[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if args.nrow is None:
        args.nrow = int(getenv("REPREP_NUP_NROW", "2"))
    if args.ncol is None:
        args.ncol = int(getenv("REPREP_NUP_NCOL", "2"))
    if args.margin is None:
        args.margin = float(getenv("REPREP_NUP_MARGIN", "10.0"))
    if args.page_format is None:
        args.page_format = getenv("REPREP_NUP_PAGE_FORMAT", "A4-L")
    nup_pdf(args.path_src, args.path_dst, args.nrow, args.ncol, args.margin, args.page_format)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-nup-pdf", description="Put multiple pages per sheet using a fixed layout."
    )
    parser.add_argument("path_src", help="The source pdf to which notes should be added.")
    parser.add_argument("path_dst", help="The output pdf.")
    parser.add_argument(
        "-r",
        "--nrow",
        help="The number of rows. "
        "The default is ${REPREP_NUP_NROW} or 2 if the variable is not set.",
        type=int,
    )
    parser.add_argument(
        "-c",
        "--ncol",
        help="The number of columns. "
        "The default is ${REPREP_NUP_NCOL} or 2 if the variable is not set.",
        type=int,
    )
    parser.add_argument(
        "-m",
        "--margin",
        help="The margin in mm. "
        "The default is ${REPREP_NUP_MARGIN} or 10.0 if the variable is not set.",
        type=float,
    )
    parser.add_argument(
        "-p",
        "--page-format",
        help="The output page format. "
        "The default is ${REPREP_NUP_PAGE_FORMAT} or A4-L if the variable is not set.",
    )
    return parser.parse_args(argv)


def nup_pdf(
    path_src: str,
    path_dst: str,
    nrow: int,
    ncol: int,
    margin: float,
    page_format: str,
):
    """Put multiple pages in a single page, using a fixed layout.

    Parameters
    ----------
    path_src
        The source PDF filename.
    path_dst
        The destination PDF filename.
    nrow
        The number of rows in the layout.
    ncol
        The number of columns in the layout.
    margin
        The margin and (minimal) spacing between small pages in millimeter.
    page_format
        A string describing the output page size.
    """
    for path_pdf in path_src, path_dst:
        if not path_pdf.endswith(".pdf"):
            raise ValueError(f"All arguments must have a `.pdf` extension, got: {path_pdf}")
    src = pymupdf.open(path_src)
    # See https://github.com/pymupdf/PyMuPDF/issues/3635
    src.scrub()
    dst = pymupdf.open()

    nup = nrow * ncol
    unit = 72 / 25.4
    # Convert distances in mm to points
    margin *= unit
    width, height = pymupdf.paper_size(page_format)

    # Spacing between two top-left corners of neighboring panels.
    xshift = (width - margin) / ncol
    yshift = (height - margin) / nrow

    for icoarse in range(0, len(src), nup):
        dst_page = dst.new_page(width=width, height=height)
        for ifine in range(icoarse, min(icoarse + nup, len(src))):
            ioffset = ifine - icoarse
            irow = ioffset // ncol
            icol = ioffset % ncol
            dst_page.show_pdf_page(
                pymupdf.Rect(
                    margin + xshift * icol,
                    margin + yshift * irow,
                    xshift * (icol + 1),
                    yshift * (irow + 1),
                ),
                src,
                ifine,
            )

    # Strip metadata for reproducibility and save
    dst.set_metadata({})
    dst.del_xml_metadata()
    dst.xref_set_key(-1, "ID", "null")
    dst.scrub()
    dst.save(path_dst, garbage=4, deflate=True, no_new_id=True)

    dst.close()
    src.close()


if __name__ == "__main__":
    main()
