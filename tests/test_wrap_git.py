# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.wrap_git."""

import os
import subprocess

import pytest

from stepup.core.path import Path
from stepup.reprep.wrap_git import amend_head_inputs

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Tester",
    "GIT_AUTHOR_EMAIL": "tester@no-email.com",
    "GIT_COMMITTER_NAME": "Tester",
    "GIT_COMMITTER_EMAIL": "tester@no-email.com",
}


def git(workdir: Path, *args: str) -> str:
    """Run a git command and return its standard output."""
    cp = subprocess.run(
        ["git", *args],
        cwd=workdir,
        env=os.environ | GIT_ENV,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        text=True,
    )
    return cp.stdout


def init_repo(path: Path, *init_args: str) -> Path:
    """Create a git repository with one commit on the branch `main`."""
    path.makedirs_p()
    git(path, "init", "--initial-branch=main", *init_args)
    git(path, "commit", "--allow-empty", "-m", "First commit")
    return path


@pytest.fixture
def amended(monkeypatch) -> list[list[str]]:
    """Record the input paths of every call to `amend()` in `stepup.reprep.wrap_git`."""
    calls = []

    def fake_amend(*, inp):
        calls.append([str(path) for path in ([inp] if isinstance(inp, str) else inp)])

    monkeypatch.setattr("stepup.reprep.wrap_git.amend", fake_amend)
    return calls


def same_files(actual: list[list[str]], expected: list[list[str]]) -> bool:
    """Compare lists of paths, also when one is relative and the other absolute."""
    if [len(paths) for paths in actual] != [len(paths) for paths in expected]:
        return False
    return all(
        os.path.samefile(path_a, path_e)
        for paths_a, paths_e in zip(actual, expected, strict=True)
        for path_a, path_e in zip(paths_a, paths_e, strict=True)
    )


def test_symbolic_head(path_tmp: Path, amended, monkeypatch):
    repo = init_repo(path_tmp / "repo")
    monkeypatch.chdir(repo)
    amend_head_inputs()
    assert amended == [[".git/HEAD"], [".git/refs/heads/main"]]


def test_symbolic_head_subdir(path_tmp: Path, amended, monkeypatch):
    repo = init_repo(path_tmp / "repo")
    (repo / "sub").makedirs_p()
    monkeypatch.chdir(repo / "sub")
    amend_head_inputs()
    assert amended == [["../.git/HEAD"], ["../.git/refs/heads/main"]]


def test_detached_head(path_tmp: Path, amended, monkeypatch):
    repo = init_repo(path_tmp / "repo")
    git(repo, "checkout", "--detach")
    monkeypatch.chdir(repo)
    amend_head_inputs()
    assert amended == [[".git/HEAD"]]


def test_packed_refs(path_tmp: Path, amended, monkeypatch):
    repo = init_repo(path_tmp / "repo")
    git(repo, "pack-refs", "--all")
    monkeypatch.chdir(repo)
    amend_head_inputs()
    assert amended == [[".git/HEAD"], [".git/packed-refs", ".git/logs/HEAD"]]


def test_packed_refs_without_reflog(path_tmp: Path, amended, monkeypatch):
    repo = path_tmp / "repo"
    repo.makedirs_p()
    git(repo, "init", "--initial-branch=main")
    git(repo, "config", "core.logAllRefUpdates", "false")
    git(repo, "commit", "--allow-empty", "-m", "First commit")
    git(repo, "pack-refs", "--all")
    monkeypatch.chdir(repo)
    amend_head_inputs()
    assert amended == [[".git/HEAD"], [".git/packed-refs"]]


def test_worktree(path_tmp: Path, amended, monkeypatch):
    repo = init_repo(path_tmp / "repo")
    git(repo, "worktree", "add", "-b", "feature", "../wt")
    monkeypatch.chdir(path_tmp / "wt")
    amend_head_inputs()
    # The worktree has its own HEAD, while its branch is stored in the common git directory.
    assert same_files(
        amended,
        [[repo / ".git/worktrees/wt/HEAD"], [repo / ".git/refs/heads/feature"]],
    )


def test_worktree_detached(path_tmp: Path, amended, monkeypatch):
    repo = init_repo(path_tmp / "repo")
    git(repo, "worktree", "add", "--detach", "../wt")
    monkeypatch.chdir(path_tmp / "wt")
    amend_head_inputs()
    assert same_files(amended, [[repo / ".git/worktrees/wt/HEAD"]])


def supports_reftable() -> bool:
    cp = subprocess.run(
        ["git", "init", "-h"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        text=True,
    )
    return "--ref-format" in cp.stdout + cp.stderr


@pytest.mark.skipif(not supports_reftable(), reason="git without the reftable ref format")
def test_reftable(path_tmp: Path, amended, monkeypatch):
    repo = init_repo(path_tmp / "repo", "--ref-format=reftable")
    monkeypatch.chdir(repo)
    with pytest.raises(RuntimeError, match="reftable"):
        amend_head_inputs()
