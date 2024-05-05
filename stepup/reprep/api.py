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

from collections.abc import Collection

from path import Path

from stepup.core.api import getenv, pool, step, subs_env_vars
from stepup.core.utils import make_path_out

__all__ = (
    "cat_pdf",
    "check_hrefs",
    "convert_markdown",
    "convert_weasyprint",
    "convert_odf_pdf",
    "convert_pdf",
    "convert_pdf_png",
    "convert_svg",
    "convert_svg_pdf",
    "convert_svg_png",
    "latex",
    "latex_diff",
    "latex_flat",
    "make_manifest",
    "nup_pdf",
    "raster_pdf",
    "render",
    "zip_manifest",
)


def add_notes_pdf(
    path_src: str, path_notes: str, path_dst: str, optional: bool = False, block: bool = False
):
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
    """
    step(
        "python -m stepup.reprep.add_notes_pdf ${inp} ${out}",
        inp=[path_src, path_notes],
        out=path_dst,
        optional=optional,
        block=block,
    )


def cat_pdf(
    paths_inp: Collection[str],
    path_out: str,
    *,
    mutool: str | None = None,
    optional: bool = False,
    block: bool = False,
):
    """Concatenate the pages of multiple PDFs into one document

    Parameters
    ----------
    paths_inp
        The input PDF files.
    path_out
        The concatenated PDF.
    mutool
        The path to the mutool executable.
        Defaults to `${REPREP_MUTOOL}` variable or `mutool` if the variable is unset.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.
    """
    if mutool is None:
        mutool = getenv("REPREP_MUTOOL", "mutool")
    step(
        mutool + " merge -o ${out} ${inp}",
        inp=paths_inp,
        out=path_out,
        optional=optional,
        block=block,
    )


def check_hrefs(path_src: str, path_config: str | None = None, block: bool = False):
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
    """
    with subs_env_vars() as subs:
        path_src = subs(path_src)
        path_config = subs(path_config)
    command = f"python -m stepup.reprep.check_hrefs {path_src}"
    inp_paths = [path_src]
    if path_config is not None:
        inp_paths.append(path_config)
        command += f" -c {path_config}"
    step(command, inp=inp_paths, block=block)


pool("markdown", 1)


def convert_markdown(
    path_md: str,
    out: str | None = None,
    *,
    optional: bool = False,
    block: bool = False,
):
    """Convert a markdown to HTML.

    Parameters
    ----------
    path_md
        The markdown input file.
    out
        Output destination: `None`, a directory or a file.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.
    """
    with subs_env_vars() as subs:
        path_md = subs(path_md)
        out = subs(out)
    if not path_md.endswith(".md"):
        raise ValueError("The Markdown file must have extension .md")
    path_html = make_path_out(path_md, out, ".html")
    command = "python -m stepup.reprep.convert_markdown ${inp} ${out}"
    step(command, inp=path_md, out=path_html, pool="markdown", optional=optional, block=block)


def convert_weasyprint(
    path_html: str,
    out: str | None = None,
    *,
    optional: bool = False,
    block: bool = False,
):
    """Convert a HTML document to PDF.

    Parameters
    ----------
    path_html
        The HTML input file.
    out
        Output destination: `None`, a directory or a file.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.
    """
    with subs_env_vars() as subs:
        path_html = subs(path_html)
        out = subs(out)
    if not path_html.endswith(".html"):
        raise ValueError("The HTML file must have extension .html")
    path_pdf = make_path_out(path_html, out, ".pdf")
    command = "weasyprint ${inp} ${out}"
    step(command, inp=path_html, out=path_pdf, optional=optional, block=block)


def convert_odf_pdf(
    path_odf: str,
    out: str | None = None,
    *,
    libreoffice: str | None = None,
    optional: bool = False,
    block: bool = False,
):
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
        f"WORK=`mktemp -d --suffix=reprep` && {libreoffice} "
        "-env:UserInstallation=file://${WORK} --convert-to pdf ${inp} --outdir ${WORK} "
        "> /dev/null && cp ${WORK}/*.pdf ${out} && rm -r ${WORK}"
    )
    path_pdf = make_path_out(path_odf, out, ".pdf")
    step(command, inp=path_odf, out=path_pdf, optional=optional, block=block)


def convert_pdf(
    path_pdf: str,
    path_out: str,
    *,
    resolution: int | None = None,
    mutool: str | None = None,
    optional: bool = False,
    block: bool = False,
):
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
    """
    if resolution is None:
        resolution = int(getenv("REPREP_CONVERT_PDF_RESOLUTION", "100"))
    if mutool is None:
        mutool = getenv("REPREP_MUTOOL", "mutool")
    step(
        f"{mutool} draw -q -o ${{out}} -r {resolution} ${{inp}}",
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
):
    """Shorthand for `convert_pdf` with the output file derived from the PDF file.

    The `out` argument can be `None`, a directory or a file. See `make_path_out`.
    """
    with subs_env_vars() as subs:
        path_pdf = subs(path_pdf)
        out = subs(out)
    if not path_pdf.endswith(".pdf"):
        raise ValueError("The PDF file must have extension .pdf")
    path_png = make_path_out(path_pdf, out, ".png")
    convert_pdf(
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
):
    """Convert an SVG figure to a PDF file, detecting dependencies of the SVG on other files.

    Parameters
    ----------
    path_svg
        The input SVG figure. It may contain <img> tags referring to other files included in
        the figure.
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
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.

    Notes
    -----
    A wrapper around inkscape is used to carry out the conversion: `stepup.reprep.convert_svg_pdf`.
    The wrapper scans the SVG for dependencies, which may be a bit slow in case of large files.
    Inkscape is executed in a separate step inside a single-core pool to work around
    the following bug: https://gitlab.com/inkscape/inkscape/-/issues/4716
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        path_out = subs(path_out)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    elif not (path_out.endswith(".pdf") or path_out.endswith(".png")):
        raise ValueError("The output file must have extension .pdf or .png")
    command = f"python -m stepup.reprep.convert_inkscape {path_svg} {path_out}"
    if inkscape is not None:
        command += f" --inkscape={inkscape}"
    if inkscape_args is not None:
        command += f" -- {inkscape_args}"
    if optional:
        command += " --optional"
    step(command, inp=path_svg, block=block)


def convert_svg_pdf(
    path_svg: str,
    out: str | None = None,
    *,
    inkscape: str | None = None,
    inkscape_args: str | None = None,
    optional: bool = False,
    block: bool = False,
):
    """Shorthand for `convert_svg` with the output file derived from the SVG file.

    The `out` argument can be `None`, a directory or a file.
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        out = subs(out)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    path_pdf = make_path_out(path_svg, out, ".pdf")
    convert_svg(
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
):
    """Shorthand for `convert_svg` with the output file derived from the SVG file.

    The `out` argument can be `None`, a directory or a file. See `make_path_out`.
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        out = subs(out)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    path_png = make_path_out(path_svg, out, ".png")
    convert_svg(
        path_svg,
        path_png,
        inkscape=inkscape,
        inkscape_args=inkscape_args,
        optional=optional,
        block=block,
    )


def latex(
    path_tex: str,
    run_bibtex=True,
    maxrep: int = 5,
    workdir: str = "./",
    *,
    latex: str | None = None,
    bibtex: str | None = None,
    bibsane: str | None = None,
    bibsane_config: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> str:
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
    path_pdf
        The PDF file being created, relative to the working directory.
    """
    with subs_env_vars() as subs:
        path_tex = subs(path_tex)
    if not path_tex.endswith(".tex"):
        raise ValueError(f"The input of the latex command must end with .tex, got {path_tex}.")

    prefix = path_tex[:-4]
    path_pdf = f"{prefix}.pdf"

    workdir = Path(workdir)
    command = f"python -m stepup.reprep.latex {path_tex}"
    inp_paths = [workdir / path_tex]
    if maxrep != 5:
        command += f" --maxrep={maxrep}"
    if latex is not None:
        command += f" --latex={latex}"
    if run_bibtex:
        command += " --run-bibtex"
        if bibtex is not None:
            command += f" --bibtex={bibtex}"
        if bibsane is not None:
            command += f" --bibsane={bibsane}"
        if bibsane_config is not None:
            command += f" --bibsane-config={bibsane_config}"
            inp_paths.append(workdir / bibsane_config)
    step(
        command,
        inp=inp_paths,
        out=[workdir / path_pdf, workdir / f"{prefix}.aux", workdir / f"{prefix}.MANIFEST.txt"],
        workdir=workdir,
        optional=optional,
        block=block,
    )
    return workdir / path_pdf


DEFAULT_LATEXDIFF_ARGS = (
    "--append-context2cmd=abstract,supplementary,dataavailability,funding,"
    "authorcontributions,conflictsofinterest,abbreviations"
)


def latex_diff(
    path_old: str,
    path_new: str,
    path_diff: str,
    *,
    latexdiff: str | None = None,
    latexdiff_args: str | None = DEFAULT_LATEXDIFF_ARGS,
    optional: bool = False,
    block: bool = False,
):
    """Create a step to run latexdiff.

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
        --append-context2cmd=abstract,supplementary,dataavailability,funding, \\
                             authorcontributions,conflictsofinterest,abbreviations
        ```

        The option `--no-label` is always added because it is needed to make the file reproducible.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.
    """
    if latexdiff is None:
        latexdiff = getenv("REPREP_LATEXDIFF", "latexdiff")

    if latexdiff_args is None:
        latexdiff_args = getenv("REPREP_LATEXDIFF_ARGS", "")

    step(
        f"{latexdiff} {latexdiff_args} ${{inp}} --no-label > ${{out}}",
        inp=[path_old, path_new],
        out=path_diff,
        optional=optional,
        block=block,
    )


def latex_flat(path_tex: str, path_flat: str, *, optional: bool = False, block: bool = False):
    """Flatten structured LaTeX source files (substitute `\\input` and friends by their content).

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
    """
    step(
        "python -m stepup.reprep.latex_flat ${inp} ${out}",
        inp=path_tex,
        out=path_flat,
        optional=optional,
        block=block,
    )


def make_manifest(
    path_manifest: str, paths: Collection[str] = (), *, optional: bool = False, block: bool = False
):
    """Create a `MANIFEST.txt` file.

    Parameters
    ----------
    path_manifest
        This can be either a `MANIFEST.in` file, in which case it is processed and a corresponding
        `MANIFEST.out` is created. The same syntax is used as in setuptools.
        See https://setuptools.pypa.io/en/latest/userguide/miscellaneous.html
        The other option is to provide a `MANIFEST.txt` file, which serves as output.
        In this case, no `MANIFEST.in` is processed.
        The distinction between the two is based on the file extension.
    paths
        (Additional) paths to include in the `MANIFEST.txt` file.
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.
    """
    if path_manifest.endswith(".in"):
        path_txt = path_manifest[:-3] + ".txt"
        step(
            "reprep-make-manifest -i ${inp}",
            inp=[path_manifest, *paths],
            out=[path_txt],
            optional=optional,
            block=block,
        )
    elif path_manifest.endswith(".txt"):
        step(
            "reprep-make-manifest ${inp} -o ${out}",
            inp=paths,
            out=[path_manifest],
            optional=optional,
            block=block,
        )
    else:
        raise ValueError("The path_manifest argument must either have the .in or .txt suffix")


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
):
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
    """
    command = "python -m stepup.reprep.nup_pdf ${inp} ${out}"
    if nrow is not None:
        command += f" -r {nrow}"
    if ncol is not None:
        command += f" -c {ncol}"
    if margin is not None:
        command += f" -m {margin}"
    if page_format is not None:
        command += f" -p {page_format}"
    step(command, inp=path_src, out=path_dst, optional=optional, block=block)


def raster_pdf(
    path_inp: str,
    out: str,
    *,
    resolution: int | None = None,
    quality: int | None = None,
    optional: bool = False,
    block: bool = False,
):
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
    """
    command = "python -m stepup.reprep.raster_pdf ${inp} ${out}"
    if resolution is not None:
        command += f" -r {resolution}"
    if quality is not None:
        command += f" -q {quality}"
    path_out = make_path_out(path_inp, out, ".pdf")
    step(command, inp=path_inp, out=path_out, optional=optional, block=block)


def render(
    path_template: str,
    paths_variables: list[str],
    out: str,
    *,
    mode: str = "auto",
    optional: bool = False,
    block: bool = False,
):
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
    """
    if mode not in ["auto", "plain", "latex"]:
        raise ValueError(f"Unsupported mode {mode!r}. Must be one of 'auto', 'plain', 'latex'")
    if len(paths_variables) == 0:
        raise ValueError("At least one file with variable definitions needed.")
    path_out = make_path_out(path_template, out, None)
    command = "python -m stepup.reprep.render ${inp} ${out}"
    if mode != "auto":
        command += f" --mode {mode}"
    step(
        command,
        inp=[path_template, *paths_variables],
        out=path_out,
        optional=optional,
        block=block,
    )


def zip_manifest(path_manifest: str, path_zip: str, *, optional: bool = False, block: bool = False):
    """Create a ZIP file with all files listed in a `MANIFEST.txt` file + check digests before zip.

    Parameters
    ----------
    path_manifest
        A file created with the `make_manifest` API or with the command-line script
        `reprep-make-manifest`.
    path_zip
        The output ZIP file
    optional
        When `True`, the step is only executed when needed by other steps.
    block
        When `True`, the step will always remain pending.
    """
    step(
        "python -m stepup.reprep.zip_manifest ${inp} ${out}",
        inp=path_manifest,
        out=path_zip,
        optional=optional,
        block=block,
    )
