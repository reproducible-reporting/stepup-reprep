# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.jupyter_kernel"""

import os
import shutil
import subprocess

import pytest
from nbformat import read, v4, write
from path import Path

from stepup.reprep.jupyter_kernel import ipc_kernel_config

TRANSPORT_SOURCE = """\
from ipykernel.kernelapp import IPKernelApp

print("transport:", IPKernelApp.instance().transport)
"""
"""Source of a notebook cell that prints the transport of the kernel it runs in."""

needs_jupyter = pytest.mark.skipif(not shutil.which("jupyter"), reason="No Jupyter")


def test_ipc_kernel_config():
    with ipc_kernel_config() as config:
        assert config.KernelManager.transport == "ipc"
        assert os.path.isabs(config.KernelManager.ip)
        path_dir = os.path.dirname(config.KernelManager.ip)
        assert os.path.isdir(path_dir)
        assert os.path.dirname(config.KernelManager.connection_file) == path_dir
    assert not os.path.exists(path_dir)


def run_tool(*args: str):
    """Run one of the RepRep command-line tools in a subprocess, as StepUp does.

    The `main` functions are deliberately not called in process.
    The synchronous Jupyter API creates an asyncio event loop that it never closes
    (observed with jupyter-core 5.9.1),
    and the socket pair of such a loop makes Python emit a `ResourceWarning`
    when the garbage collector eventually reclaims the loop.
    That happens at an unpredictable moment,
    so in process it would turn an arbitrary later test into a failure.
    """
    subprocess.run(args, stdin=subprocess.DEVNULL, check=True)


def write_transport_notebook(path_nb: Path):
    """Write a notebook whose only cell prints the transport of its kernel."""
    notebook = v4.new_notebook(cells=[v4.new_code_cell(TRANSPORT_SOURCE)])
    notebook.metadata.kernelspec = {
        "name": "python3",
        "language": "python",
        "display_name": "Python 3",
    }
    with open(path_nb, "w") as fh:
        write(notebook, fh)


@needs_jupyter
def test_convert_jupyter_ipc(path_tmp: Path):
    path_nb = path_tmp / "transport.ipynb"
    write_transport_notebook(path_nb)
    path_out = path_tmp / "transport.md"
    run_tool("srr-convert-jupyter", path_nb, path_out, "--to", "markdown", "--execute")
    assert "transport: ipc" in path_out.read_text()


@needs_jupyter
def test_execute_papermill_ipc(path_tmp: Path):
    path_nb = path_tmp / "transport.ipynb"
    write_transport_notebook(path_nb)
    path_out = path_tmp / "transport_out.ipynb"
    run_tool("srr-execute-papermill", path_nb, path_out)
    notebook = read(path_out, as_version=4)
    (cell,) = [cell for cell in notebook.cells if cell.source == TRANSPORT_SOURCE]
    (output,) = cell.outputs
    assert output.text.strip() == "transport: ipc"
