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
"""Run examples."""

import os
import re
import shutil
import subprocess

import pytest
from path import Path

from stepup.reprep.pytest import run_example

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


def has_texlive_2023():
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
    return match.group("year") == "2023"


@pytest.mark.skipif(not has_texlive_2023(), reason="No TeX Live 2023")
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


@pytest.mark.skipif(not shutil.which("inkscape"), reason="No Inkscape")
@pytest.mark.parametrize(
    "name",
    [
        "convert_inkscape",
        pytest.param("convert_inkscape_concurrency", marks=pytest.mark.heavy),
        "tile_pdf",
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


@pytest.mark.skipif(not shutil.which("typst"), reason="No Typst")
@pytest.mark.parametrize(
    "name",
    [
        "compile_typst_args",
        "compile_typst_dep",
        pytest.param("compile_typst_dep_error", marks=pytest.mark.xfail),
        "compile_typst_error",
        "compile_typst_external",
        "compile_typst_png",
        "compile_typst_png_multi",
        "compile_typst_relpath",
        "compile_typst_simple",
        "compile_typst_svg",
        "compile_typst_svg_deps",
        "compile_typst_svg_multi",
        "compile_typst_sysinp",
        "compile_typst_sysinp_json",
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
