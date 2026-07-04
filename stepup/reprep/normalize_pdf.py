# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Remove trailer ID and flaky metadata to make PDFs reproducible."""

import argparse
import shutil
import tempfile

import fitz
from path import Path

__all__ = ("pdf_normalize",)


def main():
    """Main program."""
    pdf_normalize(parse_args().path_pdf)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(prog="srr-normalize-pdf", description="Normalize a PDF file.")
    parser.add_argument("path_pdf", help="The pdf to be normalized (in place).")
    return parser.parse_args()


def pdf_normalize(path_pdf: str):
    """Replace a PDF file by its normalized equivalent. This helps making PDFs reproducible."""
    if not path_pdf.endswith(".pdf"):
        raise ValueError(f"The input must have a `.pdf` extension, got: {path_pdf}")
    pdf = fitz.open(path_pdf)
    pdf.set_metadata({})
    pdf.del_xml_metadata()
    pdf.xref_set_key(-1, "ID", "null")
    pdf.scrub()
    with tempfile.TemporaryDirectory(suffix="srr-normalize-pdf", prefix="rr") as dn:
        path_out = Path(dn) / "out.pdf"
        pdf.save(path_out, garbage=4, deflate=True, no_new_id=True)
        pdf.close()
        shutil.copy(path_out, path_pdf)


if __name__ == "__main__":
    main()
