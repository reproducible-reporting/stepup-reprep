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
"""Application programming interface for StepUp RepRep."""

import json
import shlex
from collections.abc import Collection

from path import Path

from stepup.core.api import StepInfo, getenv, step, subs_env_vars
from stepup.core.utils import make_path_out, string_to_bool

__all__ = (
    "add_notes_pdf",
    "cat_pdf",
    "check_hrefs",
    "compile_latex",
    "compile_typst",
    "convert_inkscape",
    "convert_inkscape_pdf",
    "convert_inkscape_png",
    "convert_jupyter",
    "convert_markdown",
    "convert_mutool",
    "convert_mutool_png",
    "convert_odf_pdf",
    "convert_weasyprint",
    "diff_latex",
    "flatten_latex",
    "make_inventory",
    "nup_pdf",
    "raster_pdf",
    "render_jinja",
    "sanitize_bibtex",
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
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

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
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    args = ["rr-cat-pdf", "${inp}", "${out}"]
    if insert_blank:
        args.append("--insert-blank")
    return step(
        " ".join(args),
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
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_src = subs(path_src)
        path_config = subs(path_config)
    args = ["rr-check-hrefs", shlex.quote(path_src)]
    inp_paths = [path_src]
    if path_config is not None:
        inp_paths.append(path_config)
        args.extend(["-c", path_config])
    return step(" ".join(args), inp=inp_paths, block=block)


def compile_latex(
    path_tex: str,
    *,
    run_bibtex=True,
    maxrep: int = 5,
    workdir: str = "./",
    latex: str | None = None,
    bibtex: str | None = None,
    inventory: str | bool | None = None,
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
    inventory
        If set to a `str`, it specifies the inventory file to write.
        If set to  `True`, the inventory file is written to the default location,
        which is the stem of the source file with `-inventory.txt` appended.
        When the environment variable `REPREP_LATEX_INVENTORY` is set to `1`,
        the inventory file is always written, unless this argument is set to `False`.
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
    The LaTeX source is compiled with the `rr-compile-latex` command,
    which can detect dependencies on other files by scanning for
    `\\input`, `\\include`, `\\includegraphics`, etc.
    Due to the complexity of LaTeX, the dependency scanning is not perfect.
    You can manually specify dependencies in the LaTeX source with `%REPREP input inp_path`.
    When `inp_path` is a relative path,
    it is interpreted in the same way as the LaTeX compiler would resolve it.
    You can also hide lines from the dependency scanner by adding `%REPREP ignore`.
    """
    with subs_env_vars() as subs:
        path_tex = subs(path_tex)
    if not path_tex.endswith(".tex"):
        raise ValueError(f"The input of the latex command must end with .tex, got {path_tex}.")

    prefix = path_tex[:-4]
    path_pdf = f"{prefix}.pdf"

    args = ["rr-compile-latex", shlex.quote(path_tex)]
    inp_paths = [path_tex]
    out_paths = [path_pdf, f"{prefix}.aux", f"{prefix}.fls"]
    if maxrep != 5:
        args.append("--maxrep=" + shlex.quote(str(maxrep)))
    if latex is not None:
        args.append("--latex=" + shlex.quote(latex))
    if run_bibtex:
        args.append("--run-bibtex")
        if bibtex is not None:
            args.append("--bibtex=" + shlex.quote(bibtex))
    if inventory is None:
        inventory = string_to_bool(getenv("REPREP_LATEX_INVENTORY", "0"))
    if inventory is True:
        inventory = f"{prefix}-inventory.txt"
    if isinstance(inventory, str):
        args.append("--inventory=" + shlex.quote(inventory))
        out_paths.append(inventory)
    return step(
        " ".join(args),
        inp=inp_paths,
        out=out_paths,
        workdir=workdir,
        optional=optional,
        block=block,
    )


def compile_typst(
    path_typ: str,
    dest: str | None = None,
    *,
    sysinp: dict[str, str | Path] | None = None,
    resolution: int | None = None,
    workdir: str = "./",
    typst: str | None = None,
    keep_deps: bool = False,
    typst_args: Collection[str] = (),
    inventory: str | bool | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Create a step for the compilation of a Typst source.

    !!! warning

        This feature will only work well with typst 0.13 or later.

        Support for typst in StepUp RepRep is experimental.
        Expect breaking changes in future releases.
        Some limitations include:

        - The relative paths in the depfile written by typst are inconsistent.
          A workaround is implemented in RepRep, which can hopefully be removed in the future.
          https://github.com/typst/typst/issues/5857
        - Multi-page SVG and PNG outputs are not yet supported,
          due to a bug in the depfile created by typst.
          https://github.com/typst/typst/issues/5861
        - SVG figures with references to external bitmaps are not processed correctly.
          These bitmaps are not rendered, neither are they included in the dep file.
          For this probem, a workaround was suggsted here:
          https://github.com/typst/typst/issues/5335
        - When the typst compiler detects an error in the input, it doesn't write the dep file.
          This means that StepUp cannot reschedule it, even if that would fix the problem.
          (If it would know which files are used, it would see which ones are outdated,
          rebuild them and then retry the typst command.)

    Parameters
    ----------
    path_typ
        The main typst source file.
        This argument may contain environment variables.
    dest
        Output destination: `None`, a directory or a file.
        For SVG and PNG outputs, this argument must be specified with the desired extension.
        If the output contains any of `{p}`, `{0p}` or `{t}`, the output paths are not
        known a priori and will be amended.
    sysinp
        A dictionary with the input arguments passed to `typst`with `--input key=val`.
        Keys and values are converted to strings.
        When values are `Path` instances, they are treated as input dependencies for the step.
        These parameters are available in the document as `#sys.inputs.key`.
    resolution
        The resolution of the bitmap in dots per inch (dpi),
        only relevant for PNG output.
    workdir
        The working directory where the LaTeX command must be executed.
    typst
        Path to the Typst executable.
        Defaults to `${REPREP_TYPST}` variable or `typst` if the variable is unset.
    keep_deps
        If `True`, the dependency file is kept after the compilation.
        The dependency file is also kept if the environment variable
        `REPREP_KEEP_TYPST_DEPS` is set to `"1"`.
    typst_args
        Additional arguments for typst.
        The defaults is `${REPREP_TYPST_ARGS}`, if the environment variable is defined.
    inventory
        If set to a `str`, it specifies the inventory file to write.
        If set to  `True`, the inventory file is written to the default location,
        which is the stem of the source file with `-inventory.txt` appended.
        When the environment variable `REPREP_TYPST_INVENTORY` is set to `1`,
        the inventory file is always written, unless this argument is set to `False`.
    optional
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_typ = subs(path_typ)
        dest = subs(dest)
    if not path_typ.endswith(".typ"):
        raise ValueError(f"The input of the typst command must end with .typ, got {path_typ}.")
    path_out = make_path_out(path_typ, dest, ".pdf", [".svg", ".png"])

    stem = path_typ[:-4]
    args = ["rr-compile-typst"]
    if resolution is not None:
        args.append(f"--resolution={shlex.quote(str(resolution))}")
    if typst is not None:
        args.append(f"--typst={shlex.quote(typst)}")
    paths_out = []
    if not any(x in path_out for x in ("{p}", "{0p}", "{t}")):
        paths_out.append(path_out)
    if keep_deps or string_to_bool(getenv("REPREP_KEEP_TYPST_DEPS", "0")):
        args.append("--keep-deps")
        paths_out.append(f"{stem}.dep")
    if inventory is None:
        inventory = string_to_bool(getenv("REPREP_TYPST_INVENTORY", "0"))
    if inventory is True:
        inventory = f"{stem}-inventory.txt"
    if isinstance(inventory, str):
        args.append(f"--inventory={shlex.quote(inventory)}")
        paths_out.append(inventory)
    args.append(shlex.quote(path_typ))
    if path_typ[:-4] != path_out[:-4]:
        args.append("--out=" + shlex.quote(path_out))
    path_inp = [path_typ]
    if sysinp is not None and len(sysinp) > 0:
        args.append("--sysinp")
        for key, val in sysinp.items():
            args.append(shlex.quote(str(key)) + "=" + shlex.quote(str(val)))
            if isinstance(val, Path):
                path_inp.append(val)
    if len(typst_args) > 0:
        args.append("--")
        args.extend(shlex.quote(typst_arg) for typst_arg in typst_args)

    return step(
        " ".join(args),
        inp=path_inp,
        out=paths_out,
        workdir=workdir,
        optional=optional,
        block=block,
    )


def convert_inkscape(
    path_svg: str,
    path_out: str,
    *,
    inkscape: str | None = None,
    inkscape_args: Collection[str] = (),
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
        Additional arguments to pass to inkscape. E.g. `["-T"]` to convert text to glyphs in PDFs.
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
    A wrapper around inkscape is used to carry out the conversion: `stepup.reprep.convert_inkscape`.
    The wrapper scans the SVG for dependencies, which may be a bit slow in case of large files.
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        path_out = subs(path_out)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    if not path_out.endswith((".pdf", ".png")):
        raise ValueError("The output file must have extension .pdf or .png")
    args = ["rr-convert-inkscape", shlex.quote(path_svg), shlex.quote(path_out)]
    if inkscape is not None:
        args.append("--inkscape=" + shlex.quote(inkscape))
    if len(inkscape_args) > 0:
        args.append("--")
        args.extend(shlex.quote(inkscape_arg) for inkscape_arg in inkscape_args)
    return step(" ".join(args), inp=path_svg, out=path_out, block=block, optional=optional)


def convert_inkscape_pdf(
    path_svg: str,
    dest: str | None = None,
    *,
    inkscape: str | None = None,
    inkscape_args: Collection[str] = (),
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Shorthand for `convert_inkscape` with the output file derived from the SVG file.

    The `dest` argument can be `None`, a directory or a file.
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        dest = subs(dest)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    path_pdf = make_path_out(path_svg, dest, ".pdf")
    return convert_inkscape(
        path_svg,
        path_pdf,
        inkscape=inkscape,
        inkscape_args=inkscape_args,
        optional=optional,
        block=block,
    )


def convert_inkscape_png(
    path_svg: str,
    dest: str | None = None,
    *,
    inkscape: str | None = None,
    inkscape_args: Collection[str] = (),
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Shorthand for `convert_inkscape` with the output file derived from the SVG file.

    The `dest` argument can be `None`, a directory or a file. See `make_path_out`.
    """
    with subs_env_vars() as subs:
        path_svg = subs(path_svg)
        dest = subs(dest)
    if not path_svg.endswith(".svg"):
        raise ValueError("The SVG file must have extension .svg")
    path_png = make_path_out(path_svg, dest, ".png")
    return convert_inkscape(
        path_svg,
        path_png,
        inkscape=inkscape,
        inkscape_args=inkscape_args,
        optional=optional,
        block=block,
    )


def convert_jupyter(
    path_nb: str,
    dest: str | None = None,
    *,
    inp: str | Collection[str] = (),
    out: str | Collection[str] = (),
    execute: bool = True,
    to: str | None = None,
    nbargs: str | dict | list | None = None,
    jupyter: str | None = None,
    optional: bool = False,
    pool: str | None = None,
    block: bool = False,
) -> StepInfo:
    """Convert a Jupyter notebook, by default to HTML with execution of cells.

    !!! warning

        Support for `juptyer nbconvert` in StepUp RepRep is experimental.
        Expect breaking changes in future releases.

    Parameters
    ----------
    path_nb
        The input Jupyter notebook.
    dest
        Output destination: `None`, a directory or a file.
    inp
        One or more input files used by the notebook.
        You can also declare inputs with `amend(inp=...)` in the notebook,
        but specifying them here will make the scheduling more efficient.
    out
        One or more output files produced by the notebook.
        You can also declare outputs with `amend(out=...)` in the notebook,
        but you can specify them here if you want to make the notebook execution optional,
        i.e. dependent on whether the outputs are used in other steps.
    execute
        If `True`, the notebook is executed before conversion.
    to
        The output format. The default depends on the extension of the output file.
        if `to` is given and `dest` is `None` or a directory,
        the `to` argument is used to determine the output file extension.
    nbargs
        If `str`, it is passed literally as additional argument to the notebook
        through the environment variable `REPREP_NBARGS`.
        If `dict` or `list`, it is converted to a JSON string first.
        The notebook should read this variable with `os.getenv("REPREP_NBARGS")`
        and not `stepup.core.api.getenv()` because the variable is local to the process.
        It is impossible (and pointless) for the StepUp director to detect changes in this variable.
        Even if it is globally defined, it will be overridden in this step.
    jupyter
        The path to the jupyter executable.
        Defaults to `${REPREP_JUPYTER}` variable or `jupyter` if the variable is unset.
    optional
        If `True`, the step is only executed when needed by other steps.
    pool
        The pool in which the step is executed,
        which may be convenient to limit the number of parallel notebooks being executed,
        e.g. when the already run calculations in parallel.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_nb = subs(path_nb)
        dest = subs(dest)
    if not path_nb.endswith(".ipynb"):
        raise ValueError("The notebook file must have extension .ipynb")
    if isinstance(inp, str):
        inp = [inp]
    if isinstance(out, str):
        out = [out]
    default_exts = {
        "html": ".html",
        "pdf": ".pdf",
        "notebook": ".ipynb",
        "latex": ".tex",
        "markdown": ".md",
        "rst": ".rst",
        "script": ".py",
        "asciidoc": ".txt",
    }
    if to is not None:
        default_ext = default_exts.get(to)
        if default_ext is None:
            raise ValueError(f"Unsupported output format: {to}")
    else:
        default_ext = ".html"
    other_exts = [".html", ".pdf", ".ipynb", ".tex", ".md", ".rst", ".py", ".txt"]
    path_out = make_path_out(path_nb, dest, default_ext, other_exts)
    if to is None:
        default_formats = {val: key for key, val in default_exts.items()}
        to = default_formats[path_out.suffix]
    if jupyter is None:
        jupyter = getenv("REPREP_JUPYTER", "jupyter")
    args = [jupyter, "nbconvert", shlex.quote(path_nb), "--stdout", "--to", to]
    if execute:
        args.append("--execute")
    if nbargs is not None:
        if isinstance(nbargs, dict | list):
            nbargs = json.dumps(nbargs)
        elif not isinstance(nbargs, str):
            nbargs = str(nbargs)
        args.insert(0, "REPREP_NBARGS=" + shlex.quote(nbargs))
    args.extend([">", shlex.quote(path_out)])
    step(
        " ".join(args),
        inp=[path_nb, *inp],
        out=[path_out, *out],
        optional=optional,
        pool=pool,
        block=block,
    )


def convert_markdown(
    path_md: str,
    dest: str | None = None,
    *,
    paths_css: str | Collection[str] = (),
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Convert a markdown to HTML.

    Parameters
    ----------
    path_md
        The markdown input file.
    dest
        Output destination: `None`, a directory or a file.
    paths_css
        Path or multiple paths of a local CSS file, or a list of multiple such paths,
        to be included in the HTML header.
        Note that one may also specify CSS file in the markdown header.
        Defaults to `${REPREP_MARKDOWN_CSS}` if the variable is set,
        which is interpreted as a colon-separated list of files.
    optional
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_md = subs(path_md)
        dest = subs(dest)
    if not path_md.endswith(".md"):
        raise ValueError("The Markdown file must have extension .md")
    path_html = make_path_out(path_md, dest, ".html")
    inp = [path_md]
    args = ["rr-convert-markdown", shlex.quote(path_md), shlex.quote(path_html)]
    if len(paths_css) > 0:
        if isinstance(paths_css, str):
            paths_css = [paths_css]
        args.append("--css")
        args.extend(shlex.quote(path_css) for path_css in paths_css)
        inp.extend(paths_css)
    return step(" ".join(args), inp=inp, out=path_html, optional=optional, block=block)


def convert_mutool(
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
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

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
    return step(
        " ".join(args),
        inp=path_pdf,
        out=path_out,
        optional=optional,
        block=block,
    )


def convert_mutool_png(
    path_pdf: str,
    dest: str | None = None,
    *,
    resolution: int | None = None,
    mutool: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Shorthand for `convert_mutool` with the output file derived from the PDF file.

    The `dest` argument can be `None`, a directory or a file. See `make_path_out`.
    """
    with subs_env_vars() as subs:
        path_pdf = subs(path_pdf)
        dest = subs(dest)
    if not path_pdf.endswith(".pdf"):
        raise ValueError("The PDF file must have extension .pdf")
    path_png = make_path_out(path_pdf, dest, ".png")
    return convert_mutool(
        path_pdf, path_png, resolution=resolution, mutool=mutool, optional=optional, block=block
    )


def convert_weasyprint(
    path_html: str,
    dest: str | None = None,
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
    dest
        Output destination: `None`, a directory or a file.
    weasyprint
        The path to the weasyprint executable.
        Defaults to `${REPREP_WEASYPRINT}` variable or `weasyprint` if the variable is unset.
    optional
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_html = subs(path_html)
        dest = subs(dest)
    if not path_html.endswith(".html"):
        raise ValueError("The HTML file must have extension .html")
    path_pdf = make_path_out(path_html, dest, ".pdf")
    args = ["rr-convert-weasyprint", shlex.quote(path_html), shlex.quote(path_pdf)]
    if weasyprint is not None:
        args.append("--weasyprint=" + shlex.quote(weasyprint))
    return step(" ".join(args), inp=path_html, out=path_pdf, block=block, optional=optional)


def convert_odf_pdf(
    path_odf: str,
    dest: str | None = None,
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
    dest
        None, output directory or path. See `make_path_out`.
    libreoffice
        The libreoffice executable.
        Defaults to `${REPREP_LIBREOFFICE}` variable or `libreoffice` if the variable is unset.
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
    This function does not yet scan the source document for reference to external files.
    which should ideally be added as dependencies.
    """
    with subs_env_vars() as subs:
        path_odf = subs(path_odf)
        dest = subs(dest)
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
    path_pdf = make_path_out(path_odf, dest, ".pdf")
    return step(command, inp=path_odf, out=path_pdf, optional=optional, block=block)


DEFAULT_LATEXDIFF_ARGS = (
    "--append-context2cmd=abstract,supplementary,dataavailability,funding,"
    "authorcontributions,conflictsofinterest,abbreviations",
)


def diff_latex(
    path_old: str,
    path_new: str,
    path_diff: str,
    *,
    latexdiff: str | None = None,
    latexdiff_args: Collection[str] = DEFAULT_LATEXDIFF_ARGS,
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
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    if latexdiff is None:
        latexdiff = getenv("REPREP_LATEXDIFF", "latexdiff")

    if latexdiff_args is None:
        latexdiff_args = shlex.split(getenv("REPREP_LATEXDIFF_ARGS", ""))

    args = [shlex.quote(latexdiff)]
    args.extend(shlex.quote(latexdiff_arg) for latexdiff_arg in latexdiff_args)
    args.extend(["${inp}", "--no-label", ">", "${out}"])
    return step(
        " ".join(args),
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
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

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
    *paths: Collection[str],
    path_def: str | None = None,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Create an `inventory.txt` file.

    Parameters
    ----------
    paths
        Paths to include in the `inventory.txt` file,
        except for the last, which is the inventory file to write.
    path_def
        An inventory definitions file, used to constructe the list of files.
    optional
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    if len(paths) < 1:
        raise ValueError("At least one path must be given.")
    paths_inp = list(paths[:-1])
    args = ["rr-make-inventory", *paths_inp]
    if path_def is not None:
        args.extend(["-i", path_def])
        paths_inp.append(path_def)
    args.extend(["-o", paths[-1]])
    return step(
        shlex.join(args),
        inp=paths_inp,
        out=[paths[-1]],
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
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    args = ["rr-nup-pdf", "${inp}", "${out}"]
    if nrow is not None:
        args.extend(["-r", str(nrow)])
    if ncol is not None:
        args.extend(["-c", str(ncol)])
    if margin is not None:
        args.extend(["-m", str(margin)])
    if page_format is not None:
        args.extend(["-p", shlex.quote(page_format)])
    return step(" ".join(args), inp=path_src, out=path_dst, optional=optional, block=block)


def raster_pdf(
    path_inp: str,
    dest: str,
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
    dest
        None, output directory or path. See `make_path_out`.
    resolution
        The resolution of the bitmap in dots per inch (dpi).
        The default value is taken from `${REPREP_RASTER_RESOLUTION}` or 100 if the variable is not
        set.
    quality
        The JPEG quality of the bitmap.
        The default value is taken from `${REPREP_RASTER_QUALITY}` or 50 if the variable is not set.
    optional
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    args = ["rr-raster-pdf", "${inp}", "${out}"]
    if resolution is not None:
        args.extend(["-r", str(resolution)])
    if quality is not None:
        args.extend(["-q", shlex.quote(str(quality))])
    path_out = make_path_out(path_inp, dest, ".pdf")
    return step(" ".join(args), inp=path_inp, out=path_out, optional=optional, block=block)


def render_jinja(
    *args: str | dict,
    mode: str = "auto",
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Render the template with Jinja2.

    Parameters
    ----------
    args
        The first argument is the path to the template file.
        All the following position arguments can be one of the following two types:

        - Paths to Python, JSON or YAML files with variable definitions.
          Variables defined in later files take precedence.
        - A dictionary with additional variables.
          These will be JSON-serialized and passed on the command-line to the Jinja renderer.
          Variables in dictionaries take precedence over variables from files.
          When multiple dictionaries are given, later ones take precedence.

        The very last argument is an output destination (directory or file).
    mode
        The format of the Jinja placeholders.
        The default (auto) selects either plain or latex based on the extension of the template.
        The plain format is the default Jinja style with curly brackets: {{ }} etc.
        The latex style replaces curly brackets by angle brackets: << >> etc.
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
    At least some variables must be given, either as a file containing variables or as a dictionary.
    """
    # Parse the positional arguments
    if len(args) < 3:
        raise ValueError(
            "At least three positional arguments must be given: "
            "the template, at least one file or dict with variables, and the destination."
        )
    path_template = args[0]
    if not isinstance(path_template, str):
        raise TypeError("The template argument must be a string.")
    dest = args[-1]
    if not isinstance(dest, str):
        raise TypeError("The destination argument must be a string.")
    variables = {}
    paths_variables = []
    for arg in args[1:-1]:
        if isinstance(arg, str):
            paths_variables.append(arg)
        elif isinstance(arg, dict):
            variables.update(arg)
        else:
            raise TypeError("The variables arguments must be strings (paths) or dictionaries.")

    # Parse other arguments.
    if mode not in ["auto", "plain", "latex"]:
        raise ValueError(f"Unsupported mode {mode!r}. Must be one of 'auto', 'plain', 'latex'")
    if len(paths_variables) == 0 and len(variables) == 0:
        raise ValueError("At least one file with variable definitions needed.")
    path_out = make_path_out(path_template, dest, None)

    # Create the command
    args = ["rr-render-jinja", "${inp}", "${out}"]
    if mode != "auto":
        args.append(f"--mode={mode}")
    if len(variables) > 0:
        args.append("--json=" + shlex.quote(json.dumps(variables)))
    return step(
        " ".join(args),
        inp=[path_template, *paths_variables],
        out=path_out,
        optional=optional,
        block=block,
    )


def sanitize_bibtex(
    *paths_aux: str,
    path_cfg: str | None = None,
    path_out: str | None = None,
    overwrite: bool = False,
    optional: bool = False,
    block: bool = False,
) -> StepInfo:
    """Sanitize a BibTeX file.

    Parameters
    ----------
    paths_aux
        Paths to LaTeX aux files.
    path_cfg
        The YAML configuration file for the `rr-sanitize-bibtex` script.
    path_out
        If given, a single cleaned-up bibtex file is written as output,
        which you can manually copy back to the original if you approve of the cleanup.
        If not given, the original bibtex file is overwritten (if there is only one),
        which will drain the scheduler.
        You then check if the updated version is correct and rerun the build to approve.
    overwrite
        If `True`, it is assumed that you want to overwrite an input bibtex file,
        in which case `path_out` is not treated as a new output file in the workflow.
    optional
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    with subs_env_vars() as subs:
        path_cfg = subs(path_cfg)
        paths_aux = [subs(path_aux) for path_aux in paths_aux]
        path_out = subs(path_out)

    args = ["rr-bibsane", "--amend", *(shlex.quote(path_aux) for path_aux in paths_aux)]
    paths_inp = list(paths_aux)
    if path_cfg is not None:
        args.append("--config=" + shlex.quote(path_cfg))
        paths_inp.append(path_cfg)
    paths_out = []
    if path_out is not None:
        args.append("--out=" + shlex.quote(path_out))
        if not overwrite:
            paths_out.append(path_out)
    return step(" ".join(args), inp=paths_inp, out=paths_out, optional=optional, block=block)


def sync_zenodo(path_config: str, *, block: bool = False) -> StepInfo:
    """Synchronize data with an draft dataset on Zenodo.

    Parameters
    ----------
    path_config
        The YAML configuration file for the Zenodo upload.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    return step("rr-sync-zenodo ${inp}", inp=path_config, block=block)


def unplot(
    path_svg: str, dest: str | None = None, *, optional: bool = False, block: bool = False
) -> StepInfo:
    """Convert a plot back to data.

    Parameters
    ----------
    path_svg
        The SVG file with paths to be converted back.
    dest
        An output directory or file.

    optional
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

    Returns
    -------
    step_info
        Holds relevant information of the step, useful for defining follow-up steps.
    """
    path_out = make_path_out(path_svg, dest, ".json")
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
        If `True`, the step is only executed when needed by other steps.
    block
        If `True`, the step will always remain pending.

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
