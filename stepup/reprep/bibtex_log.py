# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
r"""Identification of errors in BibTeX logs."""

from .latex_log import DEFAULT_MESSAGE, ErrorInfo


def parse_bibtex_log(path_blg: str) -> ErrorInfo | None:
    """Parse a BibTeX log file.

    Parameters
    ----------
    path_blg
        The blg file.

    Returns
    -------
    error_info
        Structured info for printing error, or None
    """
    last_src = "(could not detect source file)"
    error = False
    recorded = []
    with open(path_blg, errors="ignore") as fh:
        for line in fh.readlines():
            if "---" in line and "file " in line:
                last_src = line.rsplit(maxsplit=1)[-1]
                recorded = []
            recorded.append(line[:-1])
            if line.startswith("I'm skipping whatever remains"):
                error = True
                break
            if line.startswith(r"I found no \bibstyle command"):
                last_src = line.split()[-1]
                recorded = [line[:-1]]
                error = True
                break

    message = "\n".join(recorded) if error else DEFAULT_MESSAGE.format(path=path_blg)
    return ErrorInfo("BibTeX", last_src, message=message)
