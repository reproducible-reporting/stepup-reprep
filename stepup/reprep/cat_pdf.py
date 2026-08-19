# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Concatenate multiple PDFs into a single document, optionally inserting blank pages."""

import argparse
import sys

import fitz

__all__ = ("cat_pdf", "main")


def main():
    """Main program."""
    args = parse_args()
    cat_pdf(args.paths_src, args.path_dst, args.insert_blank)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-cat-pdf", description="Concatenate PDFs, optionally inserting blank pages."
    )
    parser.add_argument("paths_src", help="The source PDFs to concatenate.", nargs="+")
    parser.add_argument("path_dst", help="The output PDF.")
    parser.add_argument(
        "-i",
        "--insert-blank",
        help="Insert a blank page after a PDF with an odd number of pages. "
        "The last page of each PDF is used to determine the size of the added blank page.",
        default=False,
        action="store_true",
    )
    return parser.parse_args()


def cat_pdf(
    paths_src: list[str],
    path_dst: str,
    insert_blank: bool,
):
    """Concatenate PDFs into a single document.

    Parameters
    ----------
    paths_src
        The source PDF filenames, in the order they are concatenated.
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
    main()
