# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Configuration of the Jupyter kernels launched by StepUp RepRep."""

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from traitlets.config import Config

__all__ = ("ipc_kernel_config",)


@contextmanager
def ipc_kernel_config() -> Iterator[Config]:
    """Configure a Jupyter kernel to use ZeroMQ IPC sockets in a private temporary directory.

    With the default TCP transport, `jupyter_client` selects free ports
    by binding sockets to port zero and releasing them again,
    so two kernels starting at the same time may select the same port
    and one of them fails with "Address already in use".
    IPC sockets are files in a directory used by a single process only,
    which cannot collide.

    Yields
    ------
    config
        A traitlets configuration to pass as the `config` argument
        of an `nbclient.NotebookClient` subclass.
        The temporary directory is removed when the context manager exits.
    """
    with tempfile.TemporaryDirectory(prefix="srr-jupyter-") as tmpdir:
        config = Config()
        config.KernelManager.transport = "ipc"
        # With the IPC transport, ip is a path prefix:
        # the five channels become {ip}-1 up to {ip}-5.
        # It must be absolute, because the kernel runs in the directory of the notebook,
        # while the kernel manager searches for unused socket names in its own directory.
        config.KernelManager.ip = str(Path(tmpdir) / "socket")
        config.KernelManager.connection_file = str(Path(tmpdir) / "connection.json")
        yield config
