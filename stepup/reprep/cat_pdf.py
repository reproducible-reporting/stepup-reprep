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
"""Concatenate multiple PDFs into a single document, optionally inserting blank pages."""

import argparse
import sys

import fitz

__all__ = ("cat_pdf",)


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    cat_pdf(args.paths_src, args.path_dst, args.insert_blank)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-cat-pdf", description="Concatenate PDFs, optionally inserting blank pages."
    )
    parser.add_argument(
        "paths_src", help="The source PDFs to which notes should be added.", nargs="+"
    )
    parser.add_argument("path_dst", help="The output PDF.")
    parser.add_argument(
        "-i",
        "--insert-blank",
        help="Insert a blank page after a PDF with an odd number of pages. "
        "The last page of each PDF is used to determine the size of the added blank page.",
        default=False,
        action="store_true",
    )
    return parser.parse_args(argv)


def cat_pdf(
    paths_src: list[str],
    path_dst: str,
    insert_blank: bool,
):
    """Put multiple pages in a single page, using a fixed layout.

    Parameters
    ----------
    paths_src
        The source PDF filename.
    path_dst
        The destination PDF filename.
    insert_blank
        Insert a blank page after a PDF with an odd number of pages.
        The last page of each PDF is used to determine the size of the added blank page.
    """
    for path_pdf in [*paths_src, path_dst]:
        if not path_pdf.endswith(".pdf"):
            raise ValueError(
                f"All arguments must have a `.pdf` extension, got: {path_pdf}", file=sys.stderr
            )
    dst = fitz.open()

    for path_src in paths_src:
        src = fitz.open(path_src)
        # See https://github.com/pymupdf/PyMuPDF/issues/3635
        src.scrub()
        dst.insert_pdf(src)
        if insert_blank and src.page_count % 2 == 1:
            last_page = src[-1]
            dst.insert_page(-1, width=last_page.rect.width, height=last_page.rect.height)
        src.close()

    # Strip metadata for reproducibility and save
    dst.set_metadata({})
    dst.del_xml_metadata()
    dst.xref_set_key(-1, "ID", "null")
    dst.scrub()
    dst.save(path_dst, garbage=4, deflate=True, no_new_id=True)

    dst.close()


if __name__ == "__main__":
    main(sys.argv[1:])
