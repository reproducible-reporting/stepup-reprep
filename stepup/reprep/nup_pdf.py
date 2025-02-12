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
"""Put multiple pages per sheet using a fixed layout."""

import argparse
import sys

import fitz

from stepup.core.api import getenv

__all__ = ("nup_pdf",)


def main(argv: list[str] | None = None):
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-nup-pdf", description="Put multiple pages per sheet using a fixed layout."
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
            raise ValueError(
                f"All arguments must have a `.pdf` extension, got: {path_pdf}", file=sys.stderr
            )
    src = fitz.open(path_src)
    # See https://github.com/pymupdf/PyMuPDF/issues/3635
    src.scrub()
    dst = fitz.open()

    nup = nrow * ncol
    unit = 72 / 25.4
    # Convert distances in mm to points
    margin *= unit
    width, height = fitz.paper_size(page_format)

    # Spacing between two top-left corners of neighboring panels.
    xshift = (width - margin) / ncol
    yshift = (height - margin) / nrow

    # double loop adding all (small) pages to the destination PDF.
    for icoarse in range(0, len(src), nup):
        dst_page = dst.new_page(width=width, height=height)
        for ifine in range(icoarse, min(icoarse + nup, len(src))):
            ioffset = ifine - icoarse
            irow = ioffset // ncol
            icol = ioffset % ncol
            dst_page.show_pdf_page(
                fitz.Rect(
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
    main(sys.argv[1:])
