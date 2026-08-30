# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Helpers shared by `stepup.reprep.api` and the command modules."""

from collections.abc import Collection

from path import Path

from stepup.core.path import StrPath, coerce_paths

__all__ = ("MAX_NUM_ZENODO_FILES", "check_zenodo_paths")

MAX_NUM_ZENODO_FILES = 100
"""The maximum number of files that Zenodo accepts in a single record."""


def check_zenodo_paths(paths: StrPath | Collection[StrPath]) -> list[Path]:
    """Validate the list of files to be uploaded to Zenodo.

    Parameters
    ----------
    paths
        The local files to upload.

    Returns
    -------
    checked
        The same files, converted to `Path` objects.

    Raises
    ------
    ValueError
        When two files have the same name or when there are too many files.
    """
    checked = coerce_paths(paths)
    if len(checked) > MAX_NUM_ZENODO_FILES:
        raise ValueError(
            f"Zenodo accepts at most {MAX_NUM_ZENODO_FILES} files in one record, "
            f"got {len(checked)}."
        )
    seen_paths = set()
    seen_names = {}
    for path in checked:
        if path in seen_paths:
            raise ValueError(f"Duplicate paths are not allowed: {path}.")
        seen_paths.add(path)
        other = seen_names.get(path.name)
        if other is not None:
            raise ValueError(
                "Zenodo does not support directory layouts, so files must have different names. "
                f"The name {path.name} is used by {other} and {path}."
            )
        seen_names[path.name] = path
    return checked
