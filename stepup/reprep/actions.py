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
"""Actions perform the actual work in the worker processes of StepUp."""

import shlex

import attrs

from stepup.core.worker import WorkThread

from .add_notes_pdf import main as add_notes_pdf_main
from .bibsane import main as bibsane_main
from .cat_pdf import main as cat_pdf_main
from .check_hrefs import main as check_hrefs_main
from .compile_latex import main as compile_latex_main
from .compile_typst import main as compile_typst_main
from .convert_inkscape import main as convert_inkscape_main
from .convert_markdown import main as convert_markdown_main
from .convert_weasyprint import main as convert_weasyprint_main
from .execute_papermill import main as execute_papermill_main
from .flatten_latex import main as flatten_latex_main
from .make_inventory import main as make_inventory_main
from .nup_pdf import main as nup_pdf_main
from .raster_pdf import main as raster_pdf_main
from .sync_zenodo import main as sync_zenodo_main
from .unplot import main as unplot_main
from .wrap_git import main as wrap_git_main
from .zip_inventory import main as zip_inventory_main

__all__ = (
    "add_notes_pdf",
    "bibsane",
    "cat_pdf",
    "check_hrefs",
    "compile_latex",
    "compile_typst",
    "convert_inkscape",
    "convert_markdown",
    "flatten_latex",
    "make_inventory",
    "nup_pdf",
    "raster_pdf",
    "sync_zenodo",
    "unplot",
    "wrap_git",
    "zip_inventory",
)


@attrs.define
class ActionWrapper:
    """Wrapper for main functions to get support the action API."""

    main: callable

    def __call__(self, argstr: str) -> int:
        self.main(shlex.split(argstr))
        return 0


add_notes_pdf = ActionWrapper(add_notes_pdf_main)
bibsane = ActionWrapper(bibsane_main)
cat_pdf = ActionWrapper(cat_pdf_main)
check_hrefs = ActionWrapper(check_hrefs_main)
convert_markdown = ActionWrapper(convert_markdown_main)
execute_papermill = ActionWrapper(execute_papermill_main)
flatten_latex = ActionWrapper(flatten_latex_main)
make_inventory = ActionWrapper(make_inventory_main)
nup_pdf = ActionWrapper(nup_pdf_main)
raster_pdf = ActionWrapper(raster_pdf_main)
sync_zenodo = ActionWrapper(sync_zenodo_main)
unplot = ActionWrapper(unplot_main)
zip_inventory = ActionWrapper(zip_inventory_main)


@attrs.define
class WorkThreadActionWrapper:
    """Wrapper for main functions to get support the action API."""

    main: callable

    def __call__(self, argstr: str, work_thread: WorkThread) -> int:
        self.main(shlex.split(argstr), work_thread)
        return 0


compile_latex = WorkThreadActionWrapper(compile_latex_main)
compile_typst = WorkThreadActionWrapper(compile_typst_main)
convert_inkscape = WorkThreadActionWrapper(convert_inkscape_main)
convert_weasyprint = WorkThreadActionWrapper(convert_weasyprint_main)
wrap_git = WorkThreadActionWrapper(wrap_git_main)
