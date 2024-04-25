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
"""Remove trailer ID and flaky metadata to make PDFs reproducible."""

import argparse
import shutil
import sys
import tempfile

import fitz
from path import Path

__all__ = ("pdf_normalize",)


def main() -> int:
    """Main program."""
    pdf_normalize(parse_args().path_pdf)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-mupdf-normalize", description="Normalize a PDF file."
    )
    parser.add_argument("path_pdf", help="The pdf to be normalized (in place).")
    return parser.parse_args()


def pdf_normalize(path_pdf: str):
    """Replace a PDF file by its normalized equivalent. This helps making PDFs reproducible."""
    if not path_pdf.endswith(".pdf"):
        print(f"The input must have a `.pdf` extension, got: {path_pdf}", file=sys.stderr)
        return 2
    pdf = fitz.open(path_pdf)
    pdf.set_metadata({})
    pdf.del_xml_metadata()
    pdf.xref_set_key(-1, "ID", "null")
    pdf.scrub()
    with tempfile.TemporaryDirectory(suffix="reprep-normalize-pdf", prefix="rr") as dn:
        path_out = Path(dn) / "out.pdf"
        pdf.save(path_out, garbage=4, deflate=True, linear=True, no_new_id=True)
        pdf.close()
        shutil.copy(path_out, path_pdf)


if __name__ == "__main__":
    sys.exit(main())
