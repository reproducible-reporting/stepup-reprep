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
        "check_hrefs_html",
        "check_hrefs_md",
        "convert_markdown",
        "convert_weasyprint",
        "latex_flat",
        "latex_flat_subdir",
        "make_manifest_in",
        "make_manifest_in_sub",
        "make_manifest_list",
        "nup_pdf",
        "raster_pdf",
        "render_basic",
        "zip_manifest",
    ],
)
@pytest.mark.asyncio
async def test_example(tmpdir, name: str):
    await run_example(Path("tests/cases") / name, tmpdir, OVERWRITE_EXPECTED)


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
    if match.group("year") != "2023":
        return False
    return True


@pytest.mark.skipif(not has_texlive_2023(), reason="No TeX Live 2023")
@pytest.mark.parametrize(
    "name",
    [
        "check_hrefs_pdf",
        "latex_diff",
        "lualatex_simple",
        "pdflatex_bbl",
        "pdflatex_bibtex",
        "pdflatex_input",
        "render_relpath",
        "xelatex_input",
    ],
)
@pytest.mark.asyncio
async def test_latex_example(tmpdir, name: str):
    await run_example(Path("tests/cases") / name, tmpdir, OVERWRITE_EXPECTED)


@pytest.mark.skipif(not shutil.which("inkscape"), reason="No Inkscape")
@pytest.mark.parametrize(
    "name",
    ["convert_inkscape", "convert_inkscape_concurrency", "tile_pdf"],
)
@pytest.mark.asyncio
async def test_inkscape_example(tmpdir, name: str):
    await run_example(Path("tests/cases") / name, tmpdir, OVERWRITE_EXPECTED)


@pytest.mark.skipif(not shutil.which("mutool"), reason="No Mutool")
@pytest.mark.parametrize(
    "name",
    ["convert_mutool", "cat_pdf"],
)
@pytest.mark.asyncio
async def test_mutool_example(tmpdir, name: str):
    await run_example(Path("tests/cases") / name, tmpdir, OVERWRITE_EXPECTED)


@pytest.mark.skipif(not shutil.which("libreoffice"), reason="No LibreOffice")
@pytest.mark.parametrize(
    "name",
    ["convert_libreoffice", "convert_libreoffice_concurrency"],
)
@pytest.mark.asyncio
async def test_libreoffice_example(tmpdir, name: str):
    await run_example(Path("tests/cases") / name, tmpdir, OVERWRITE_EXPECTED)
