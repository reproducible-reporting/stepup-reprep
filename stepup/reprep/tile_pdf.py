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
"""Tile PDF figures."""

from collections.abc import Collection

import attrs
import fitz
import numpy as np
from scipy import optimize

__all__ = ("Figure", "Panel")


@attrs.define
class Panel:
    """The definition of one panel in a tiled figure.

    Attributes
    ----------
    irow
        The row where the panel is located (top left corner).
    icol
        The column where the panel is located (top left corner).
    label
        The label to be put above the panel.
    path_in
        The path of the PDF file with the figure.
    nrow
        The number of rows occupied by the panel.
    ncol
        The number of columns occupied by the panel.
    """

    irow: int = attrs.field()
    icol: int = attrs.field()
    label: str = attrs.field()
    path_in: str = attrs.field()
    nrow: int = attrs.field(default=1)
    ncol: int = attrs.field(default=1)
    pdf = attrs.field(default=None)


@attrs.define
class Figure:
    """The definition of a tiled figure

    Attributes
    ----------
    path_out
        The PDF output file.
    panels
        The list panels, instances of the `Panel` class.
    fontname
        A Fontname recognized by PyMyPDF or a custom name when fontfile is specified.
    fontfile
        None or the path to a ttf file.
        When used, specify a corresponding fontname (of your choice).
    fontsize
        The font size to use for the labels in points.
    label_height
        The height to use for the labels in mm.
    padding
        The padding added added to the panels before combining them, in mm.
        This parameter is also used as margin between the label and the figure.
    hshift
        An optional horizontal displacement of the panel label, in mm.
    """

    path_out: str = attrs.field()
    panels: list[Panel] = attrs.field()
    fontname: str = attrs.field(default="hebo")
    fontfile: str | None = attrs.field(default=None)
    # Dimensions in points. (1 point = 1/72 inch)
    fontsize: float = attrs.field(default=7.0)
    label_height: float = attrs.field(default=2.0)
    padding: float = attrs.field(default=1.0)
    hshift: float = attrs.field(default=0.0)

    def info(self):
        inp = [panel.path_in for panel in self.panels]
        if self.fontfile is not None:
            inp.append(self.fontfile)
        return {"inp": inp, "out": self.path_out}

    def run(self):
        """Combine PDF figures into a single PDF with labels on top of each panel."""
        _load_pdfs(self.panels)
        for panel in self.panels:
            _add_label(panel, self)
        out = _combine_figures(self.panels)
        out.set_metadata({})
        out.del_xml_metadata()
        out.scrub()
        out.save(self.path_out, garbage=4, deflate=True, no_new_id=True)


def _load_pdfs(panels: Collection[Panel]):
    for panel in panels:
        panel.pdf = fitz.open(panel.path_in)
        # See https://github.com/pymupdf/PyMuPDF/issues/3635
        panel.pdf.scrub()
        if panel.pdf.page_count != 1:
            raise ValueError(
                "Panel PDF files should have just one page. "
                f"Found {panel.pdf.page_count} in {panel.path_in}"
            )


mm = 72 / 25.4


def _add_label(panel: Panel, fig: Figure):
    new = fitz.open()
    old_page = panel.pdf[0]
    new_page = new.new_page(
        width=old_page.rect.width + 2 * fig.padding * mm,
        height=old_page.rect.height + fig.label_height * mm + 3 * fig.padding * mm,
    )
    top = fig.label_height * mm + 2 * fig.padding * mm
    new_page.show_pdf_page(
        fitz.Rect(
            fig.padding * mm,
            top,
            old_page.rect.width + fig.padding * mm,
            old_page.rect.height + top,
        ),
        panel.pdf,
        0,
    )
    font = fitz.Font(fig.fontname, fig.fontfile)
    length = font.text_length(panel.label, fontsize=fig.fontsize)
    text_writer = fitz.TextWriter(new_page.rect)
    text_writer.append(
        fitz.Point(
            (new_page.rect.width - length) / 2 + fig.hshift * mm,
            fig.padding * mm + fig.label_height * mm,
        ),
        panel.label,
        font=font,
        fontsize=fig.fontsize,
    )
    text_writer.write_text(new_page)
    panel.pdf = new


def _combine_figures(panels: list[Panel]):
    # Basic settings
    nrow = 1
    ncol = 1
    for sf in panels:
        nrow = max(nrow, sf.irow + sf.nrow)
        ncol = max(ncol, sf.icol + sf.ncol)

    # Define optimization variables
    row_vars = np.arange(nrow)
    col_vars = np.arange(ncol) + nrow
    nvar = nrow + ncol

    # Run over panels and define constraints
    a_ub = np.zeros((2 * len(panels), nvar))
    b_ub = np.zeros(2 * len(panels))
    c = np.zeros(nvar)
    c[row_vars[-1]] = 1
    c[col_vars[-1]] = 1
    ieq = 0
    for sf in panels:
        if sf.irow == 0:
            a_ub[ieq, row_vars[sf.nrow - 1]] = -1
        else:
            a_ub[ieq, row_vars[sf.irow + sf.nrow - 1]] = -1
            a_ub[ieq, row_vars[sf.irow - 1]] = 1
        b_ub[ieq] = -sf.pdf[0].rect.height
        ieq += 1
        if sf.icol == 0:
            a_ub[ieq, col_vars[sf.ncol - 1]] = -1
        else:
            a_ub[ieq, col_vars[sf.icol + sf.ncol - 1]] = -1
            a_ub[ieq, col_vars[sf.icol - 1]] = 1
        b_ub[ieq] = -sf.pdf[0].rect.width
        ieq += 1

    # Optimize the layout
    res = optimize.linprog(c, a_ub, b_ub, method="highs")
    row_pos = np.concatenate([[0.0], res.x[:nrow]])
    col_pos = np.concatenate([[0.0], res.x[nrow:]])

    # Put everything in one PDF
    out = fitz.open()
    page = out.new_page(width=col_pos[-1], height=row_pos[-1])
    for sf in panels:
        dst_rect = fitz.Rect(
            col_pos[sf.icol],
            row_pos[sf.irow],
            col_pos[sf.icol + sf.ncol],
            row_pos[sf.irow + sf.nrow],
        )
        page.show_pdf_page(dst_rect, sf.pdf, 0)
    return out
