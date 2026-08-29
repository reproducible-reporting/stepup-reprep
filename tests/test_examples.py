# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Run examples."""

import os
import re
import shutil
import subprocess

import pytest
from path import Path

from stepup.core.pytest import EXAMPLE_TIMEOUT
from stepup.reprep.pytest import run_example

pytestmark = pytest.mark.timeout(2 * EXAMPLE_TIMEOUT)
"""Budget for a whole example, which `run_example` already bounds with `EXAMPLE_TIMEOUT`.

Setup, call and teardown share this budget,
and it must stay above the deadline of the example itself,
so that a stalled example is reported with its own output instead of a bare timeout.
"""

OVERWRITE_EXPECTED = "STEPUP_OVERWRITE_EXPECTED" in os.environ


@pytest.mark.parametrize(
    "name",
    [
        "add_notes_pdf",
        "bibsane_same",
        "bibsane_other",
        "cat_pdf",
        "check_hrefs_html",
        "check_hrefs_md",
        "convert_markdown",
        pytest.param("convert_markdown_concurrency", marks=pytest.mark.heavy),
        "convert_markdown_env",
        "convert_weasyprint",
        "copy_latex_with_deps",
        "execute_papermill",
        "flatten_latex",
        "flatten_latex_subdir",
        "make_inventory_list",
        "nup_pdf",
        "raster_pdf",
        "sync_zenodo",
        "unplot",
        "wrap_git",
        "zip_def",
        "zip_inventory",
        "zip_tree",
    ],
)
@pytest.mark.asyncio
async def test_example(path_tmp, name: str):
    await run_example(Path("tests/examples") / name, path_tmp, OVERWRITE_EXPECTED)


def has_texlive_2026():
    if not shutil.which("lualatex"):
        return False
    if not shutil.which("pdflatex"):
        return False
    if not shutil.which("xelatex"):
        return False
    if not shutil.which("bibtex"):
        return False
    if not shutil.which("latexdiff"):
        return False
    cp = subprocess.run(
        ["latex", "--version"],
        stdout=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        text=True,
    )
    match = re.search(r"TeX Live (?P<year>\d\d\d\d)", cp.stdout)
    if match is None:
        return False
    return match.group("year") == "2026"


@pytest.mark.skipif(not has_texlive_2026(), reason="No TeX Live 2026")
@pytest.mark.parametrize(
    "name",
    [
        "check_hrefs_pdf",
        "diff_latex",
        "compile_lualatex_simple",
        "compile_pdflatex_bbl",
        "compile_pdflatex_bibtex",
        "compile_pdflatex_input",
        "compile_xelatex_input",
    ],
)
@pytest.mark.asyncio
async def test_latex_example(path_tmp: Path, name: str):
    await run_example(Path("tests/examples") / name, path_tmp, OVERWRITE_EXPECTED)


def has_tectonic_0_17_x():
    if not shutil.which("tectonic"):
        return False
    cp = subprocess.run(
        ["tectonic", "--version"],
        stdout=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        text=True,
    )
    return cp.stdout.split()[-1].startswith("0.17.")


@pytest.mark.skipif(not has_tectonic_0_17_x(), reason="No Tectonic 0.17.x")
@pytest.mark.parametrize(
    "name",
    [
        "compile_tectonic_bbl",
        "compile_tectonic_bibtex",
        "compile_tectonic_input",
    ],
)
@pytest.mark.asyncio
async def test_tectonic_example(path_tmp: Path, name: str):
    await run_example(Path("tests/examples") / name, path_tmp, OVERWRITE_EXPECTED)


@pytest.mark.skipif(not shutil.which("inkscape"), reason="No Inkscape")
@pytest.mark.parametrize(
    "name",
    [
        "convert_inkscape",
        pytest.param("convert_inkscape_concurrency", marks=pytest.mark.heavy),
    ],
)
@pytest.mark.asyncio
async def test_inkscape_example(path_tmp: Path, name: str):
    await run_example(Path("tests/examples") / name, path_tmp, OVERWRITE_EXPECTED)


@pytest.mark.skipif(not shutil.which("mutool"), reason="No Mutool")
@pytest.mark.parametrize(
    "name",
    ["convert_mutool"],
)
@pytest.mark.asyncio
async def test_mutool_example(path_tmp: Path, name: str):
    await run_example(Path("tests/examples") / name, path_tmp, OVERWRITE_EXPECTED)


@pytest.mark.skipif(not shutil.which("libreoffice"), reason="No LibreOffice")
@pytest.mark.parametrize(
    "name",
    [
        "convert_libreoffice",
        pytest.param("convert_libreoffice_concurrency", marks=pytest.mark.heavy),
    ],
)
@pytest.mark.asyncio
async def test_libreoffice_example(path_tmp: Path, name: str):
    await run_example(Path("tests/examples") / name, path_tmp, OVERWRITE_EXPECTED)


def has_typst_0_15():
    if not shutil.which("typst"):
        return False
    cp = subprocess.run(
        ["typst", "--version"],
        stdout=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        text=True,
    )
    return cp.stdout.split()[1].startswith("0.15.")


@pytest.mark.skipif(not has_typst_0_15(), reason="No Typst 0.15.x")
@pytest.mark.parametrize(
    "name",
    [
        "compile_typst_args",
        "compile_typst_deps",
        "compile_typst_deps_error",
        "compile_typst_error",
        "compile_typst_external",
        "compile_typst_html",
        "compile_typst_png",
        "compile_typst_png_multi",
        "compile_typst_relpath",
        "compile_typst_simple",
        "compile_typst_svg",
        "compile_typst_svg_deps",
        "compile_typst_svg_multi",
        "compile_typst_sysinp",
        "compile_typst_sysinp_json",
        "compile_typst_tile",
    ],
)
@pytest.mark.asyncio
async def test_typst_example(path_tmp: Path, name: str):
    await run_example(Path("tests/examples") / name, path_tmp, OVERWRITE_EXPECTED)


@pytest.mark.skipif(not shutil.which("jupyter"), reason="No Jupyter")
@pytest.mark.parametrize(
    "name",
    [
        "convert_jupyter",
    ],
)
@pytest.mark.asyncio
async def test_jupyter_example(path_tmp: Path, name: str):
    await run_example(Path("tests/examples") / name, path_tmp, OVERWRITE_EXPECTED)
