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
"""Application programming interface for StepUp RepRep."""

import shlex
from collections.abc import Collection

from stepup.core.api import StepInfo, getenv, step, subs_env_vars
from stepup.core.utils import make_path_out, string_to_bool

__all__ = (
    "add_notes_pdf",
    "cat_pdf",
    "check_hrefs",
    "compile_latex",
    "compile_typst",
    "convert_markdown",
    "convert_odf_pdf",
    "convert_pdf",
    "convert_pdf_png",
    "convert_svg",
    "convert_svg_pdf",
    "convert_svg_png",
    "convert_weasyprint",
    "diff_latex",
    "flatten_latex",
    "make_inventory",
    "nup_pdf",
    "raster_pdf",
    "render_jinja",
    "sync_zenodo",
    "unplot",
    "zip_inventory",
)


def add_notes_pdf(
    path_src: str, path_notes: str, path_dst: str, optional: bool = False, block: bool = False
) -> StepInfo:
    """Add a notes page at every even page of a PDF file.

    Parameters
    ----------
    path_src
        The original PDF document without notes pages.
    path_notes
        A single-page PDF document with a page suitable for taking notes.
    path_dst
        The output PDF with notes pages inserted.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    return step(
        "rr-add-notes-pdf ${inp} ${out}",
        inp=[path_src, path_notes],
        out=path_dst,
        optional=optional,
        block=block,
    )


def cat_pdf(
    paths_inp: Collection[str],
    path_out: str,
    *,
    insert_blank: bool = False,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Concatenate the pages of multiple PDFs into one document

    Parameters
    ----------
    paths_inp
        The input PDF files.
    path_out
        The concatenated PDF.
    insert_blank
        Insert a blank page after a PDF with an odd number of pages.
        The last page of each PDF is used to determine the size of the added blank page.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    command = "rr-cat-pdf"
    if insert_blank:
        command += " --insert-blank"
    command += " ${inp} ${out}"
    return step(
        command,
        inp=paths_inp,
        out=path_out,
        optional=optional,
        block=block,
    )


def check_hrefs(path_src: str, path_config: str | None = None, block: bool = False) -> StepInfo:
    """Check hyper references in a Markdown, HTML or PDF file.

    Parameters
    ----------
    path_src
        The source Markdown, HTML or PDF to check.
    path_config
        The configuration file.
        Defaults to `${REPREP_CHECK_HREFS_CONFIG}` variable or `check_hrefs.yaml` if it is not set.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_src = subs(path_src)
        path_config = subs(path_config)
    command = f"rr-check-hrefs {shlex.quote(path_src)}"
    inp_paths = [path_src]
    if path_config is not None:
        inp_paths.append(path_config)
        command += f" -c {path_config}"
    return step(command, inp=inp_paths, block=block)


def compile_latex(
    path_tex: str,
    *,
    run_bibtex=True,
    maxrep: int = 5,
    workdir: str = "./",
    latex: str | None = None,
    bibtex: str | None = None,
    bibsane: str | None = None,
    bibsane_config: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Create a step for the compilation of a LaTeX source.

    Parameters
    ----------
    path_tex
        The main tex source file.
        This argument may contain environment variables.
    run_bibtex
        By default, when bib files are used, BibTeX is invoked.
        This can be overruled by setting this argument to False,
        which is useful when recompiling sources with fixed bbl files.
    maxrep
        The maximum number of repetitions of the LaTeX command
        in case the aux file keeps changing.
    workdir
        The working directory where the LaTeX command must be executed.
    latex
        Path to the LaTeX executable. Note that only PDF-producing LaTeX compilers are supported:
        `pdflatex`, `xelatex` or `lualatex`.
        Defaults to `${REPREP_LATEX}` variable or `pdflatex` if the variable is unset.
    bibtex
        Path to the BibTeX executable.
        Defaults to `${REPREP_BIBTEX}` variable or `bibtex` if the variable is unset.
    bibsane
        Path to the BibSane executable.
        Defaults to `${REPREP_BIBSANE}` variable or `bibsane` if the variable is unset.
    bibsane_config
        Path to the BibSane configuration file.
        Defaults to `${REPREP_BIBSANE_CONFIG}` variable or `bibsane.yaml` if it is unset.
        Note that when the config file is read from the environment variable,
        it is interpreted relative to `${STEPUP_ROOT}`.
        One may define it globally with `export REPREP_BIBSANE_CONFIG='${HERE}/bibsane.yaml'`
        to refer to a local version of the file. (Mind the single quotes.)
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_tex = subs(path_tex)
    if not path_tex.endswith(".tex"):
        raise ValueError(f"The input of the latex command must end with .tex, got {path_tex}.")

    prefix = path_tex[:-4]
    path_pdf = f"{prefix}.pdf"

    command = "rr-compile-latex " + shlex.quote(path_tex)
    inp_paths = [path_tex]
    if maxrep != 5:
        command += " --maxrep=" + shlex.quote(str(maxrep))
    if latex is not None:
        command += " --latex=" + shlex.quote(latex)
    if run_bibtex:
        command += " --run-bibtex"
        if bibtex is not None:
            command += " --bibtex=" + shlex.quote(bibtex)
        if bibsane is not None:
            command += " --bibsane=" + shlex.quote(bibsane)
        if bibsane_config is not None:
            command += " --bibsane-config=" + shlex.quote(bibsane_config)
            inp_paths.append(bibsane_config)
    return step(
        command,
        inp=inp_paths,
        out=[path_pdf, f"{prefix}.aux", f"{prefix}-inventory.txt"],
        workdir=workdir,
        optional=optional,
        block=block,
    )


def compile_typst(
    path_typ: str,
    *,
    workdir: str = "./",
    typst: str | None = None,
    keep_deps: bool = False,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Create a step for the compilation of a LaTeX source.

    !!! warning

        Support for typst in StepUp RepRep is experimental.
        Expect breaking changes in future releases.
        Future extensions could include:

        - Support for inventory files, similar to `compile_latex`.
        - Support for other output formats than PDF.
        - Support for passing in other options to the typst compiler.

    Parameters
    ----------
    path_typ
        The main typst source file.
        This argument may contain environment variables.
    workdir
        The working directory where the LaTeX command must be executed.
    typst
        Path to the Typst executable.
        Defaults to `${REPREP_TYPST}` variable or `typst` if the variable is unset.
    keep_deps
        If `True`, the dependency file is kept after the compilation.
        The dependency file is also kept if the environment variable
        `REPREP_KEEP_TYPST_DEPS` is set to `"1"`.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_tex = subs(path_typ)
    if not path_typ.endswith(".typ"):
        raise ValueError(f"The input of the typst command must end with .typ, got {path_tex}.")

    stem = path_typ[:-4]
    path_pdf = f"{stem}.pdf"
    command = "rr-compile-typst "
    if typst is not None:
        command += f"--typst={shlex.quote(typst)} "
    out = [path_pdf]
    if keep_deps or string_to_bool(getenv("REPREP_KEEP_TYPST_DEPS", "0")):
        command += "--keep-deps "
        out.append(f"{stem}.dep")
    return step(
        command + shlex.quote(path_typ),
        inp=[path_typ],
        out=out,
        workdir=workdir,
        optional=optional,
        block=block,
    )


def convert_markdown(
    path_md: str,
    out: str | None = None,
    *,
    katex: bool = False,
    path_macro: str | None = None,
    paths_css: str | list[str] | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Convert a markdown to HTML.

    Parameters
    ----------
    path_md
        The markdown input file.
    out
        Output destination: `None`, a directory or a file.
    katex
        Set to `True` to enable KaTeX support.
    path_macro
        A file with macro definitions for KaTeX.
        Defaults to `${REPREP_KATEX_MACROS}` if the variable is set.
    paths_css
        Path of a local CSS file, or a list of multiple such paths,
        to be included in the HTML header.
        Note that one may also specify CSS file in the markdown header.
        Defaults to `${REPREP_MARKDOWN_CSS}` if the variable is set,
        which is interpreted as a colon-separated list of files.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_md = subs(path_md)
        out = subs(out)
    if not path_md.endswith(".md"):
        raise ValueError("The Markdown file must have extension .md")
    path_html = make_path_out(path_md, out, ".html")
    inp = [path_md]
    command = "rr-convert-markdown "
    command += shlex.join([path_md, path_html])
    if katex:
        command += " --katex"
        if path_macro is not None:
            command += " --katex-macros=" + shlex.quote(path_macro)
            inp.append(path_macro)
    if paths_css is not None:
        if isinstance(paths_css, str):
            paths_css = [paths_css]
        command += " --css " + shlex.join(paths_css)
    return step(command, inp=inp, out=path_html, optional=optional, block=block)


def convert_odf_pdf(
    path_odf: str,
    out: str | None = None,
    *,
    libreoffice: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Convert a file in OpenDocument format to PDF.

    Parameters
    ----------
    path_odf
        The input open-document file.
    out
        None, output directory or path. See `make_path_out`.
    libreoffice
        The libreoffice executable.
        Defaults to `${REPREP_LIBREOFFICE}` variable or `libreoffice` if the variable is unset.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.

    Notes
    -----
    This function does not yet scan the source document for reference to external files.
    which should ideally be added as dependencies.

    The conversion is executed in a pool of size 1, due to a bug in libreoffice.
    It cannot perform multiple PDF conversions in parallel.
    """
    with subs_env_vars() as subs:
        path_odf = subs(path_odf)
        out = subs(out)
    if libreoffice is None:
        libreoffice = getenv("REPREP_LIBREOFFICE", "libreoffice")
    command = (
        # Simple things should be simple! ;) See:
        # https://bugs.documentfoundation.org/show_bug.cgi?id=106134
        # https://bugs.documentfoundation.org/show_bug.cgi?id=152192
        # Not solved yet:
        # https://bugs.documentfoundation.org/show_bug.cgi?id=160033
        "WORK=`mktemp -d --suffix=reprep` && "
        + shlex.quote(libreoffice)
        + " -env:UserInstallation=file://${WORK} --convert-to pdf ${inp} --outdir ${WORK} "
        "> /dev/null && cp ${WORK}/*.pdf ${out} && rm -r ${WORK}"
    )
    path_pdf = make_path_out(path_odf, out, ".pdf")
    return step(command, inp=path_odf, out=path_pdf, optional=optional, block=block)


def convert_pdf(
    path_pdf: str,
    path_out: str,
    *,
    resolution: int | None = None,
    mutool: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Convert a PDF to a bitmap with mutool (from MuPDF).

    Parameters
    ----------
    path_pdf
        The input PDF file.
    path_out
        The output image file.
    resolution
        The resolution of the output bitmap in dots per inch (dpi).
    mutool
        The path to the mutool executable.
        Defaults to `${REPREP_MUTOOL}` variable or `mutool` if the variable is unset.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    if resolution is None:
        resolution = int(getenv("REPREP_CONVERT_PDF_RESOLUTION", "100"))
    if mutool is None:
        mutool = getenv("REPREP_MUTOOL", "mutool")
    args = [shlex.quote(mutool), "draw -q -o ${out} -r", shlex.quote(str(resolution)), "${inp}"]
    command = " ".join(args)
    return step(
        command,
        inp=path_pdf,
        out=path_out,
        optional=optional,
        block=block,
    )


def convert_pdf_png(
    path_pdf: str,
    out: str | None = None,
    *,
    resolution: int | None = None,
    mutool: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Shorthand for `convert_pdf` with the output file derived from the PDF file.

    The `out` argument can be `None`, a directory or a file. See `make_path_out`.
    """
    with subs_env_vars() as subs:
        path_pdf = subs(path_pdf)
        out = subs(out)
    if not path_pdf.endswith(".pdf"):
        raise ValueError("The PDF file must have extension .pdf")
    path_png = make_path_out(path_pdf, out, ".png")
    return convert_pdf(
        path_pdf, path_png, resolution=resolution, mutool=mutool, optional=optional, block=block
    )


def convert_svg(
    path_svg: str,
    path_out: str,
    *,
    inkscape: str | None = None,
    inkscape_args: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Convert an SVG figure to a PDF file, detecting dependencies of the SVG on other files.

    Parameters
    ----------
    path_svg
        The input SVG figure.
        It may contain <img> tags referring to other files included in the figure.
    path_out
        The output PDF or PNG file. Other formats are not supported.
    inkscape
        The path to the inkscape executable.
        Defaults to `${REPREP_INKSCAPE}` variable or `inkscape` if the variable is unset.
    inkscape_args
        Additional arguments to pass to inkscape. E.g. `-T` to convert text to glyphs in PDFs.
        Depending on the extension of the output, the default is `${REPREP_INKSCAPE_PDF_ARGS}` or
        `${REPREP_INKSCAPE_PNG_ARGS}`, if the environment variable is defined.
    optional
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.

    Notes
    -----
    A wrapper around inkscape is used to carry out the conversion: `stepup.reprep.convert_svg_pdf`.
    The wrapper scans the SVG for dependencies, which may be a bit slow in case of large files.
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        path_out = subs(path_out)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    if not path_out.endswith((".pdf", ".png")):
        raise ValueError("The output file must have extension .pdf or .png")
    command = "rr-convert-inkscape "
    command += shlex.join([path_svg, path_out])
    if inkscape is not None:
        command += " --inkscape=" + shlex.quote(inkscape)
    if inkscape_args is not None:
        command += f" -- {inkscape_args}"
    return step(command, inp=path_svg, out=path_out, block=block, optional=optional)


def convert_svg_pdf(
    path_svg: str,
    out: str | None = None,
    *,
    inkscape: str | None = None,
    inkscape_args: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Shorthand for `convert_svg` with the output file derived from the SVG file.

    The `out` argument can be `None`, a directory or a file.
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        out = subs(out)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    path_pdf = make_path_out(path_svg, out, ".pdf")
    return convert_svg(
        path_svg,
        path_pdf,
        inkscape=inkscape,
        inkscape_args=inkscape_args,
        optional=optional,
        block=block,
    )


def convert_svg_png(
    path_svg: str,
    out: str | None = None,
    *,
    inkscape: str | None = None,
    inkscape_args: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Shorthand for `convert_svg` with the output file derived from the SVG file.

    The `out` argument can be `None`, a directory or a file. See `make_path_out`.
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        out = subs(out)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    path_png = make_path_out(path_svg, out, ".png")
    return convert_svg(
        path_svg,
        path_png,
        inkscape=inkscape,
        inkscape_args=inkscape_args,
        optional=optional,
        block=block,
    )


def convert_weasyprint(
    path_html: str,
    out: str | None = None,
    *,
    weasyprint: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Convert a HTML document to PDF.

    Parameters
    ----------
    path_html
        The HTML input file.
    out
        Output destination: `None`, a directory or a file.
    weasyprint
        The path to the weasyprint executable.
        Defaults to `${REPREP_WEASYPRINT}` variable or `weasyprint` if the variable is unset.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_html = subs(path_html)
        out = subs(out)
    if not path_html.endswith(".html"):
        raise ValueError("The HTML file must have extension .html")
    path_pdf = make_path_out(path_html, out, ".pdf")
    command = "rr-convert-weasyprint "
    command += shlex.join([path_html, path_pdf])
    if weasyprint is not None:
        command += " --weasyprint=" + shlex.quote(weasyprint)
    if optional:
        command += " --optional"
    return step(command, inp=path_html, block=block)


DEFAULT_LATEXDIFF_ARGS = (
    "--append-context2cmd=abstract,supplementary,dataavailability,funding,"
    "authorcontributions,conflictsofinterest,abbreviations"
)


def diff_latex(
    path_old: str,
    path_new: str,
    path_diff: str,
    *,
    latexdiff: str | None = None,
    latexdiff_args: str | None = DEFAULT_LATEXDIFF_ARGS,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    r"""Create a step to run latexdiff.

    Parameters
    ----------
    path_old
        The old tex or bbl source.
    path_new
        The new tex or bbl source.
    path_diff
        The diff output tex or bbl.
    latexdiff
        Path of the latexdiff  executable.
        Defaults to `${REPREP_LATEXDIFF}` variable or `latexdiff` if the variable is unset.
    latexdiff_args
        Additional arguments for latexdiff.
        Defaults to `${REPREP_LATEXDIFF_ARG}` variable.
        If this variable is unset, the following default is used:

        ```
        --append-context2cmd=abstract,supplementary,dataavailability,funding, \
                             authorcontributions,conflictsofinterest,abbreviations
        ```

        The option `--no-label` is always added because it is needed to make the file reproducible.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    if latexdiff is None:
        latexdiff = getenv("REPREP_LATEXDIFF", "latexdiff")

    if latexdiff_args is None:
        latexdiff_args = getenv("REPREP_LATEXDIFF_ARGS", "")

    args = [shlex.quote(latexdiff), latexdiff_args, "${inp}", "--no-label", ">", "${out}"]
    command = " ".join(args)
    return step(
        command,
        inp=[path_old, path_new],
        out=path_diff,
        optional=optional,
        block=block,
    )


def flatten_latex(path_tex: str, path_flat: str, *, optional: bool = False, block: bool = False):
    r"""Flatten structured LaTeX source files (substitute `\input` and friends by their content).

    Parameters
    ----------
    path_tex
        The main tex file to be converted.
    path_flat
        The flattened output file.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    return step(
        "rr-flatten-latex ${inp} ${out}",
        inp=path_tex,
        out=path_flat,
        optional=optional,
        block=block,
    )


def make_inventory(
    paths: Collection[str], path_inventory: str, *, optional: bool = False, block: bool = False
) -> StepInfo:
    """Create an `inventory.txt` file.

    Parameters
    ----------
    paths
        Paths to include in the `inventory.txt` file.
    path_inventory
        The inventory file to write.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    return step(
        "rr-make-inventory ${inp} -o ${out}",
        inp=paths,
        out=[path_inventory],
        optional=optional,
        block=block,
    )


def nup_pdf(
    path_src: str,
    path_dst: str,
    *,
    nrow: int | None = None,
    ncol: int | None = None,
    margin: float | None = None,
    page_format: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Put multiple pages per sheet using a fixed layout.

    Parameters
    ----------
    path_src
        The original PDF document (with normal pages).
    path_dst
        The output PDF with (multiple pages per sheet).
    nrow
        The number of rows on each output sheet.
        The default is `${REPREP_NUP_NROW}` or 2 if the variable is not set.
    ncol
        The number of columns on each output sheet.
        The default is `${REPREP_NUP_NCOL}` or 2 if the variable is not set.
    margin
        The margin in mm between the pages on each sheet. (Also used as sheet margin.)
        The default is `${REPREP_NUP_MARGIN}` or 10.0 if the variable is not set.
    page_format
        The output page format
        The default is `${REPREP_NUP_PAGE_FORMAT}` or A4-L if the variable is not set.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    command = "rr-nup-pdf ${inp} ${out}"
    if nrow is not None:
        command += " -r " + shlex.quote(str(nrow))
    if ncol is not None:
        command += " -c " + shlex.quote(str(ncol))
    if margin is not None:
        command += " -m " + shlex.quote(str(margin))
    if page_format is not None:
        command += " -p " + shlex.quote(page_format)
    return step(command, inp=path_src, out=path_dst, optional=optional, block=block)


def raster_pdf(
    path_inp: str,
    out: str,
    *,
    resolution: int | None = None,
    quality: int | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Turn each page of a PDF into a rendered JPEG bitmap contained in a new PDF.

    Parameters
    ----------
    path_inp
        The input PDF file.
    out
        None, output directory or path. See `make_path_out`.
    resolution
        The resolution of the bitmap in dots per inch (pdi).
        The default value is taken from `${REPREP_RASTER_RESOLUTION}` or 100 if the variable is not
        set.
    quality
        The JPEG quality of the bitmap.
        The default value is taken from `${REPREP_RASTER_QUALITY}` or 50 if the variable is not set.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    command = "rr-raster-pdf ${inp} ${out}"
    if resolution is not None:
        command += " -r " + shlex.quote(str(resolution))
    if quality is not None:
        command += " -q " + shlex.quote(str(quality))
    path_out = make_path_out(path_inp, out, ".pdf")
    return step(command, inp=path_inp, out=path_out, optional=optional, block=block)


def render_jinja(
    path_template: str,
    paths_variables: list[str],
    out: str,
    *,
    mode: str = "auto",
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Render the template with Jinja2.

    Parameters
    ----------
    path_template
        The source file to use as a template.
    paths_variables
        A list of Python files with variable definitions, at least one.
    out
        An output directory or file.
    mode
        The format of the Jinja placeholders.
        The default (auto) selects either plain or latex based on the extension of the template.
        The plain format is the default Jinja style with curly brackets: {{ }} etc.
        The latex style replaces curly brackets by angle brackets: << >> etc.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    if mode not in ["auto", "plain", "latex"]:
        raise ValueError(f"Unsupported mode {mode!r}. Must be one of 'auto', 'plain', 'latex'")
    if len(paths_variables) == 0:
        raise ValueError("At least one file with variable definitions needed.")
    path_out = make_path_out(path_template, out, None)
    command = "rr-render-jinja ${inp} ${out}"
    if mode != "auto":
        command += f" --mode {mode}"
    return step(
        command,
        inp=[path_template, *paths_variables],
        out=path_out,
        optional=optional,
        block=block,
    )


def sync_zenodo(path_config: str, *, block: bool = False) -> StepInfo:
    """Synchronize data with an draft dataset on Zenodo.

    Parameters
    ----------
    path_config
        The YAML configuration file for the Zenodo upload.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    return step("rr-sync-zenodo ${inp}", inp=path_config, block=block)


def unplot(
    path_svg: str, out: str | None = None, *, optional: bool = False, block: bool = False
) -> StepInfo:
    """Convert a plot back to data.

    Parameters
    ----------
    path_svg
        The SVG file with paths to be converted back.
    out
        An output directory or file.

    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    path_out = make_path_out(path_svg, out, ".json")
    command = "rr-unplot ${inp} ${out}"
    return step(command, inp=path_svg, out=path_out, optional=optional, block=block)


def zip_inventory(
    path_inventory: str, path_zip: str, *, optional: bool = False, block: bool = False
) -> StepInfo:
    """Create a ZIP file with all files listed in a `inventory.txt` file + check digests before zip.

    Parameters
    ----------
    path_inventory
        A file created with the `make_inventory` API or with the command-line script
        `rr-make-inventory`.
    path_zip
        The output ZIP file
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    return step(
        "rr-zip-inventory ${inp} ${out}",
        inp=path_inventory,
        out=path_zip,
        optional=optional,
        block=block,
    )
