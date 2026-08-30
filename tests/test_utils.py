# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.utils."""

import pytest
from path import Path

from stepup.reprep.utils import MAX_NUM_ZENODO_FILES, check_zenodo_paths


def test_check_zenodo_paths_ok():
    assert check_zenodo_paths(["one.txt", "sub/two.txt"]) == [Path("one.txt"), Path("sub/two.txt")]
    assert check_zenodo_paths("one.txt") == [Path("one.txt")]
    assert check_zenodo_paths([]) == []


def test_check_zenodo_paths_duplicate():
    with pytest.raises(ValueError):
        check_zenodo_paths(["one.txt", "one.txt"])


def test_check_zenodo_paths_same_name_other_directory():
    with pytest.raises(ValueError):
        check_zenodo_paths(["sub1/one.txt", "sub2/one.txt"])


def test_check_zenodo_paths_too_many():
    paths = [f"file{i}.txt" for i in range(MAX_NUM_ZENODO_FILES)]
    assert len(check_zenodo_paths(paths)) == MAX_NUM_ZENODO_FILES
    with pytest.raises(ValueError):
        check_zenodo_paths([*paths, "extra.txt"])
