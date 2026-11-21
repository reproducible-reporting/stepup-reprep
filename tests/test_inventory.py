# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for inventory files."""

import contextlib
import hashlib
import json
import os
import stat
import zipfile

import pytest
from reprep_common import needs_symlinks

from stepup.core.path import Path
from stepup.core.platform.oscompat import file_modes_available
from stepup.reprep.check_inventory import main as check_main
from stepup.reprep.inventory import (
    HASH_ALGORITHMS,
    MAX_LINE_LENGTH,
    FileRecord,
    InventoryHeader,
    LinkRecord,
    check_record,
    compute_record,
    format_header,
    format_record,
    open_inventory,
)
from stepup.reprep.make_inventory import main as make_main
from stepup.reprep.make_inventory import parse_inventory_def, write_inventory
from stepup.reprep.pytest import mask_inventory_modes
from stepup.reprep.zip_inventory import LINK_MODE
from stepup.reprep.zip_inventory import main as zip_main


def write_text(path: str, text: str):
    """Write a text file with `\\n` line endings on every platform."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def assert_inventory(path: str, expected: str):
    """Compare an inventory file with the expected one, without file modes where files have none."""
    with open(path, encoding="utf-8", newline="") as fh:
        current = fh.read()
    if not file_modes_available():
        current = mask_inventory_modes(current)
        expected = mask_inventory_modes(expected)
    assert current == expected


def read_records(path: str) -> list[FileRecord | LinkRecord]:
    """Read all records of an inventory."""
    with open_inventory(path) as reader:
        return list(reader)


MD5_AAA = hashlib.md5(b"aaa\n").hexdigest()
MD5_BBB = hashlib.md5(b"bbb\n").hexdigest()
MD5_HEADER = '{"fields":["md5","path","size"],"format":"stepup-reprep-inventory","version":1}\n'


def test_compute_record(path_tmp):
    (path_tmp / "sub").mkdir()
    write_text(path_tmp / "sub/a.txt", "aaa\n")
    record = compute_record(path_tmp / "sub/a.txt", path_tmp / "other")
    assert record == FileRecord("../sub/a.txt", MD5_AAA, 4)


def test_compute_record_mode(path_tmp):
    write_text(path_tmp / "a.txt", "aaa\n")
    os.chmod(path_tmp / "a.txt", 0o640)
    record = compute_record(path_tmp / "a.txt", path_tmp, "sha256", mode=True)
    assert record.digest == hashlib.sha256(b"aaa\n").hexdigest()
    if file_modes_available():
        assert record.mode == "rw-r-----"
    else:
        assert len(record.mode) == 9


def test_compute_record_directory(path_tmp):
    with pytest.raises(OSError, match="Not a regular file"):
        compute_record(path_tmp, path_tmp.parent)


@pytest.mark.parametrize("modes", [True, False])
def test_check_record_modes(monkeypatch, modes: bool):
    monkeypatch.setattr("stepup.reprep.inventory.file_modes_available", lambda: modes)
    ref = FileRecord("a.txt", "0" * 32, 4, "rw-r--r--")
    other_mode = FileRecord("a.txt", "0" * 32, 4, "rw-rw-rw-")
    if modes:
        with pytest.raises(ValueError, match="File mode"):
            check_record(other_mode, ref)
    else:
        check_record(other_mode, ref)
    with pytest.raises(ValueError, match="File size"):
        check_record(FileRecord("a.txt", "0" * 32, 5, "rw-r--r--"), ref)
    with pytest.raises(ValueError, match="File digest"):
        check_record(FileRecord("a.txt", "1" * 32, 4, "rw-r--r--"), ref)


def test_check_record_without_mode():
    """A reference without permission bits ignores those of the new record."""
    check_record(FileRecord("a.txt", "0" * 32, 4, "rwxrwxrwx"), FileRecord("a.txt", "0" * 32, 4))


def test_check_record_links():
    file = FileRecord("a.txt", "0" * 32, 4)
    link = LinkRecord("a.txt", "b.txt")
    check_record(link, LinkRecord("other.txt", "b.txt"))
    with pytest.raises(ValueError, match=r"Link target should be c\.txt but got b\.txt"):
        check_record(link, LinkRecord("a.txt", "c.txt"))
    with pytest.raises(TypeError, match="Expected a symbolic link but got a regular file"):
        check_record(file, link)
    with pytest.raises(TypeError, match="Expected a regular file but got a symbolic link"):
        check_record(link, file)


BASIC_INVENTORY = f"""\
{MD5_HEADER}\
{{"md5":"{MD5_AAA}","path":"a.txt","size":4}}
{{"md5":"{MD5_BBB}","path":"b.txt","size":4}}
"""


def test_basic(path_tmp):
    with contextlib.chdir(path_tmp):
        write_text("a.txt", "aaa\n")
        write_text("b.txt", "bbb\n")
        write_text("inventory.def", "include *.txt\n")
        make_main(["-i", "inventory.def"])
        assert_inventory("inventory.jsonl", BASIC_INVENTORY)
        make_main(["-o", "inventory2.jsonl", "a.txt", "b.txt"])
        assert_inventory("inventory2.jsonl", BASIC_INVENTORY)
        check_main(["inventory.jsonl"])
        write_text("b.txt", "BBB\n")
        with pytest.raises(ValueError, match=r"File digest mismatch: b\.txt"):
            check_main(["inventory.jsonl"])


def test_output_suffix(path_tmp, capsys):
    with contextlib.chdir(path_tmp):
        write_text("a.txt", "aaa\n")
        with pytest.raises(ValueError, match=r"\.jsonl"):
            make_main(["-o", "inventory.txt", "a.txt"])
        with pytest.raises(SystemExit):
            make_main(["a.txt"])
        assert "-o option is required" in capsys.readouterr().err


def test_order(path_tmp):
    """Explicit paths come first, in the given order, then the sorted matches of the definition.

    Later duplicates are dropped after normalization.
    """
    with contextlib.chdir(path_tmp):
        for name in ["a.txt", "b.txt", "c.txt", "d.txt"]:
            write_text(name, name)
        write_text("inventory.def", "include *.txt\n")
        make_main(["c.txt", "./a.txt", "c.txt", "-i", "inventory.def"])
        paths = [record.path for record in read_records("inventory.jsonl")]
        assert paths == ["c.txt", "a.txt", "b.txt", "d.txt"]


def test_order_subdirectory(path_tmp):
    """The paths of the definition and the explicit ones are deduplicated relative to the output."""
    with contextlib.chdir(path_tmp):
        Path("sub").mkdir()
        for name in ["sub/a.txt", "sub/b.txt", "top.txt"]:
            write_text(name, name)
        write_text("sub/inventory.def", "include *.txt\n")
        make_main(["top.txt", "sub/b.txt", "-i", "sub/inventory.def"])
        paths = [record.path for record in read_records("sub/inventory.jsonl")]
        assert paths == ["../top.txt", "b.txt", "a.txt"]
        check_main(["sub/inventory.jsonl"])


@pytest.mark.parametrize("algorithm", HASH_ALGORITHMS)
def test_hash_algorithms(path_tmp, algorithm):
    with contextlib.chdir(path_tmp):
        write_text("a.txt", "aaa\n")
        make_main(["-o", "inventory.jsonl", "--hash", algorithm, "a.txt"])
        with open_inventory("inventory.jsonl") as reader:
            assert reader.header == InventoryHeader(algorithm)
            assert list(reader) == [
                FileRecord("a.txt", hashlib.new(algorithm, b"aaa\n").hexdigest(), 4)
            ]
        with open("inventory.jsonl", encoding="utf-8") as fh:
            header = json.loads(fh.readline())
        assert header["fields"] == sorted([algorithm, "path", "size"])
        check_main(["inventory.jsonl"])


def test_hash_unknown(path_tmp):
    with pytest.raises(SystemExit):
        make_main(["-o", path_tmp / "inventory.jsonl", "--hash", "shake_128", path_tmp / "a.txt"])


MODE_INVENTORY = f"""\
{{"fields":["md5","mode","path","size"],"format":"stepup-reprep-inventory","version":1}}
{{"md5":"{MD5_AAA}","mode":"rw-r--r--","path":"a.txt","size":4}}
"""


def test_mode(path_tmp):
    with contextlib.chdir(path_tmp):
        write_text("a.txt", "aaa\n")
        os.chmod("a.txt", 0o644)
        make_main(["-o", "inventory.jsonl", "--mode", "a.txt"])
        assert_inventory("inventory.jsonl", MODE_INVENTORY)
        check_main(["inventory.jsonl"])
        make_main(["-o", "inventory2.jsonl", "a.txt"])
        os.chmod("a.txt", 0o600)
        # Without --mode, the permission bits are not checked.
        check_main(["inventory2.jsonl"])
        if file_modes_available():
            with pytest.raises(ValueError, match="File mode should be rw-r--r-- but got rw-------"):
                check_main(["inventory.jsonl"])


def test_mode_skipped_without_file_modes(path_tmp, monkeypatch, capsys):
    """Without permission bits, a warning is printed and the modes are not checked."""
    monkeypatch.setattr("stepup.reprep.inventory.file_modes_available", lambda: False)
    monkeypatch.setattr("stepup.reprep.make_inventory.file_modes_available", lambda: False)
    with contextlib.chdir(path_tmp):
        write_text("a.txt", "aaa\n")
        make_main(["-o", "inventory.jsonl", "--mode", "a.txt"])
        assert "WARNING" in capsys.readouterr().err
        os.chmod("a.txt", 0o400)
        check_main(["inventory.jsonl"])


def test_deterministic(path_tmp):
    with contextlib.chdir(path_tmp):
        write_text("a.txt", "aaa\n")
        write_text("b.txt", "bbb\n")
        make_main(["-o", "inventory1.jsonl", "a.txt", "b.txt"])
        os.utime("a.txt", (0, 0))
        make_main(["-o", "inventory2.jsonl", "a.txt", "b.txt"])
        assert Path("inventory1.jsonl").read_bytes() == Path("inventory2.jsonl").read_bytes()


def test_non_ascii_path(path_tmp):
    with contextlib.chdir(path_tmp):
        write_text("Ångström λ.txt", "aaa\n")
        make_main(["-o", "inventory.jsonl", "Ångström λ.txt"])
        assert '"path":"Ångström λ.txt"' in Path("inventory.jsonl").read_text(encoding="utf-8")
        assert read_records("inventory.jsonl") == [FileRecord("Ångström λ.txt", MD5_AAA, 4)]
        check_main(["inventory.jsonl"])
        zip_main(["inventory.jsonl", "archive.zip"])
        with zipfile.ZipFile("archive.zip") as fz:
            assert fz.read("Ångström λ.txt") == b"aaa\n"


def test_format_record_mode_mismatch():
    with pytest.raises(ValueError, match="permission bits"):
        format_record(FileRecord("a.txt", "0" * 32, 4), InventoryHeader("md5", mode=True))
    with pytest.raises(ValueError, match="permission bits"):
        format_record(FileRecord("a.txt", "0" * 32, 4, "rw-r--r--"), InventoryHeader("md5"))


def test_format_header():
    assert format_header(InventoryHeader("sha256", mode=True)) == (
        '{"fields":["mode","path","sha256","size"],"format":"stepup-reprep-inventory","version":1}'
    )


SYMLINK_INVENTORY = f"""\
{MD5_HEADER}\
{{"md5":"{hashlib.md5(b"Hello").hexdigest()}","path":"dest.txt","size":5}}
{{"link":"dest.txt","path":"link.txt"}}
"""


@needs_symlinks
def test_symbolic_link(path_tmp):
    with contextlib.chdir(path_tmp):
        write_text("dest.txt", "Hello")
        Path("link.txt").symlink_to("dest.txt")
        make_main(["-o", "inventory.jsonl", "dest.txt", "link.txt"])
        assert_inventory("inventory.jsonl", SYMLINK_INVENTORY)
        check_main(["inventory.jsonl"])
        Path("link.txt").remove()
        Path("link.txt").symlink_to("other.txt")
        with pytest.raises(ValueError, match=r"Link target should be dest\.txt but got other\.txt"):
            check_main(["inventory.jsonl"])
        Path("link.txt").remove()
        write_text("link.txt", "dest.txt")
        with pytest.raises(TypeError, match="Expected a symbolic link"):
            check_main(["inventory.jsonl"])


def test_directory(path_tmp):
    with pytest.raises(ValueError):
        make_main(["-o", path_tmp / "inventory.jsonl", path_tmp])


@needs_symlinks
def test_symbolic_link_directory(path_tmp):
    path_sub = path_tmp / "sub"
    path_sub.mkdir()
    with contextlib.chdir(path_tmp):
        Path("link").symlink_to("sub", target_is_directory=True)
        with pytest.raises(ValueError):
            make_main(["-o", "inventory.jsonl", "link"])
        # Without amending, a link to a directory is recorded as a link.
        write_inventory("inventory.jsonl", ["link"], do_amend=False)
        assert read_records("inventory.jsonl") == [LinkRecord("link", "sub")]
        check_main(["inventory.jsonl"])


def test_git1():
    with contextlib.chdir("tests/examples/check_hrefs_md"):
        paths = parse_inventory_def(["include-git\n"])
    assert paths == {
        "main.sh",
        "expected_graph.txt",
        "plan.py",
        "test.md",
        "expected_stdout.txt",
        "README.txt",
        "check_hrefs.yaml",
        ".gitignore",
    }


def test_git2():
    paths = parse_inventory_def(["include-git tests/examples/check_hrefs_md\n"])
    assert paths == {
        "tests/examples/check_hrefs_md/" + path
        for path in [
            "main.sh",
            "expected_graph.txt",
            "plan.py",
            "test.md",
            "expected_stdout.txt",
            "README.txt",
            "check_hrefs.yaml",
            ".gitignore",
        ]
    }


def extract_zip(path_zip: str):
    """Extract a ZIP file in the current directory, with its file modes and symbolic links.

    `ZipFile.extract` writes a symbolic link as a file that contains the target,
    see [cpython#82102](https://github.com/python/cpython/issues/82102).
    The target of a link is stored with `/` separators,
    and Windows does not resolve a link whose target is written in that way,
    as observed on Windows 11.
    """
    with zipfile.ZipFile(path_zip) as fz:
        for info in fz.infolist():
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                os.symlink(os.path.normpath(fz.read(info).decode("utf-8")), info.filename)
            else:
                fz.extract(info)
                os.chmod(info.filename, stat.S_IMODE(mode))


@needs_symlinks
def test_zip_inventory(path_tmp):
    with contextlib.chdir(path_tmp):
        Path("sub").mkdir()
        write_text("sub/dest.txt", "Hello")
        Path("link.txt").symlink_to(os.path.normpath("sub/dest.txt"))
        make_main(["-o", "inventory.jsonl", "--mode", "sub/dest.txt", "link.txt"])
        # The target of a link is recorded and archived with `/`, also on Windows.
        assert compute_record("link.txt", ".") == LinkRecord("link.txt", "sub/dest.txt")
        check_main(["inventory.jsonl"])
        zip_main(["inventory.jsonl", "archive.zip"])
        with zipfile.ZipFile("archive.zip") as fz:
            assert fz.namelist() == ["sub/dest.txt", "link.txt"]
            assert fz.read("link.txt") == b"sub/dest.txt"
            assert fz.getinfo("link.txt").external_attr >> 16 == LINK_MODE
        Path("sub/dest.txt").remove()
        Path("sub/").rmdir()
        Path("link.txt").remove()
        extract_zip("archive.zip")
        check_main(["inventory.jsonl"])


def test_zip_outside(path_tmp):
    """A file outside the directory of the inventory cannot be zipped under its record path."""
    with contextlib.chdir(path_tmp):
        Path("sub").mkdir()
        write_text("a.txt", "aaa\n")
        make_main(["-o", "sub/inventory.jsonl", "a.txt"])
        assert read_records("sub/inventory.jsonl") == [FileRecord("../a.txt", MD5_AAA, 4)]
        check_main(["sub/inventory.jsonl"])
        with pytest.raises(ValueError, match="outside the directory of the inventory"):
            zip_main(["sub/inventory.jsonl"])
        assert not Path("sub/inventory.zip").exists()


#
# Validation of the format
#


def write_inventory_text(path_tmp: Path, text: str) -> Path:
    """Write the given text as an inventory and return its path."""
    path = path_tmp / "inventory.jsonl"
    write_text(path, text)
    return path


def test_read_missing(path_tmp):
    path = path_tmp / "inventory.jsonl"
    with pytest.raises(ValueError) as exc_info:
        read_records(path)
    assert f"The inventory {path} does not exist" in str(exc_info.value)
    assert "srr-make-inventory" in str(exc_info.value)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "\n",
        "not json\n",
        "[]\n",
        '"stepup-reprep-inventory"\n',
        '{"format":"other","version":1,"fields":["md5","path","size"]}\n',
        '{"files":[],"format":"stepup-reprep-manifest","version":"1"}\n',
        MD5_HEADER.strip(),
    ],
)
def test_read_not_an_inventory(path_tmp, text):
    path = write_inventory_text(path_tmp, text)
    with pytest.raises(ValueError) as exc_info:
        read_records(path)
    assert f"The file {path} is not an inventory written by" in str(exc_info.value)


def test_read_binary(path_tmp):
    """A binary file, here with the signature of a PNG file, is not an inventory."""
    path = path_tmp / "inventory.jsonl"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 4)
    with pytest.raises(ValueError, match="line 1 is not valid UTF-8"):
        read_records(path)


def test_read_invalid_utf8_later_line(path_tmp):
    """Invalid UTF-8 is reported on its own line, also when the file is small."""
    path = path_tmp / "inventory.jsonl"
    lines = [
        MD5_HEADER.encode(),
        f'{{"md5":"{MD5_AAA}","path":"a.txt","size":4}}\n'.encode(),
        f'{{"md5":"{MD5_AAA}","path":"b.txt","size":4}}\n'.encode(),
        f'{{"md5":"{MD5_AAA}","path":"c\xff.txt","size":4}}\n'.encode("latin-1"),
    ]
    path.write_bytes(b"".join(lines))
    with pytest.raises(ValueError, match="line 4 is not valid UTF-8"):
        read_records(path)


def test_read_long_line(path_tmp):
    """A large file without line breaks is refused without loading it."""
    path = write_inventory_text(path_tmp, "x" * (10 * MAX_LINE_LENGTH))
    with pytest.raises(ValueError, match=f"line 1 is longer than {MAX_LINE_LENGTH} bytes"):
        read_records(path)
    long_path = "a" * MAX_LINE_LENGTH
    path = write_inventory_text(
        path_tmp, MD5_HEADER + f'{{"md5":"{MD5_AAA}","path":"{long_path}","size":4}}\n'
    )
    with pytest.raises(ValueError, match="line 2 is longer than"):
        read_records(path)


@pytest.mark.parametrize("version", [2, 0, "1", 1.0, True, None])
def test_read_other_version(path_tmp, version):
    header = {"fields": ["md5", "path", "size"], "format": "stepup-reprep-inventory"}
    if version is not None:
        header["version"] = version
    path = write_inventory_text(path_tmp, json.dumps(header) + "\n")
    with pytest.raises(ValueError) as exc_info:
        read_records(path)
    assert f"has version {version!r}" in str(exc_info.value)
    assert "reads version 1" in str(exc_info.value)


def test_read_header_extra_key(path_tmp):
    path = write_inventory_text(path_tmp, MD5_HEADER.replace('"version"', '"x":0,"version"'))
    with pytest.raises(ValueError, match="the keys on line 1 are not fields, format, version"):
        read_records(path)


@pytest.mark.parametrize(
    ("fields", "match"),
    [
        ("{}", "not a list of strings"),
        ('["md5","path",3]', "not a list of strings"),
        ('["path","size"]', "exactly one hash algorithm"),
        ('["md5","path","sha256","size"]', "exactly one hash algorithm"),
        ('["path","shake_128","size"]', "exactly one hash algorithm"),
        ('["md5","path","size","x"]', "exactly one hash algorithm"),
        ('["md5","size"]', "sorted list md5, path, size"),
        ('["path","md5","size"]', "sorted list md5, path, size"),
        ('["md5","md5","path","size"]', "exactly one hash algorithm"),
        ('["md5","path","path","size"]', "sorted list md5, path, size"),
    ],
)
def test_read_header_fields(path_tmp, fields, match):
    header = MD5_HEADER.replace('["md5","path","size"]', fields)
    path = write_inventory_text(path_tmp, header)
    with pytest.raises(ValueError, match=match):
        read_records(path)


@pytest.mark.parametrize(
    "record",
    [
        "[]",
        "7",
        f'{{"path":"a.txt","size":4,"sha256":"{MD5_AAA}"}}',
        f'{{"md5":"{MD5_AAA}","path":"a.txt"}}',
        f'{{"md5":"{MD5_AAA}","mode":"rw-r--r--","path":"a.txt","size":4}}',
    ],
)
def test_read_record_keys(path_tmp, record):
    path = write_inventory_text(path_tmp, MD5_HEADER + record + "\n")
    with pytest.raises(
        ValueError, match="line 2 is not a JSON object with the keys md5, path, size"
    ):
        read_records(path)


@pytest.mark.parametrize(
    "record",
    ['{"link":"a.txt","path":"b.txt","size":4}', '{"link":"a.txt"}'],
)
def test_read_link_keys(path_tmp, record):
    path = write_inventory_text(path_tmp, MD5_HEADER + record + "\n")
    with pytest.raises(ValueError, match="line 2 is a link without exactly the keys link, path"):
        read_records(path)


@pytest.mark.parametrize("target", ["", 7, None])
def test_read_link_target(path_tmp, target):
    record = json.dumps({"link": target, "path": "a.txt"})
    path = write_inventory_text(path_tmp, MD5_HEADER + record + "\n")
    with pytest.raises(ValueError, match="link target on line 2 is not a non-empty string"):
        read_records(path)


@pytest.mark.parametrize(
    ("value", "match"),
    [
        ("", "is not a non-empty string"),
        (7, "is not a non-empty string"),
        (None, "is not a non-empty string"),
        (["a.txt"], "is not a non-empty string"),
        ("/a.txt", "is absolute"),
        ("C:/a.txt", "is absolute"),
        ("//server/share/a.txt", "is absolute"),
        ("sub\\a.txt", "contains a backslash"),
        ("./a.txt", "is not the normalized path of a file"),
        ("sub/../a.txt", "is not the normalized path of a file"),
        ("sub//a.txt", "is not the normalized path of a file"),
        ("sub/", "is not the normalized path of a file"),
        (".", "is not the normalized path of a file"),
        ("..", "is not the normalized path of a file"),
        ("../..", "is not the normalized path of a file"),
    ],
)
def test_read_record_path(path_tmp, value, match):
    record = json.dumps({"md5": MD5_AAA, "path": value, "size": 4})
    path = write_inventory_text(path_tmp, MD5_HEADER + record + "\n")
    with pytest.raises(ValueError, match=f"the path on line 2 {match}"):
        read_records(path)


def test_read_record_path_outside(path_tmp):
    """A path starting with `../` is valid in an inventory."""
    record = json.dumps({"md5": MD5_AAA, "path": "../../a.txt", "size": 4})
    path = write_inventory_text(path_tmp, MD5_HEADER + record + "\n")
    assert read_records(path) == [FileRecord("../../a.txt", MD5_AAA, 4)]


@pytest.mark.parametrize("value", [MD5_AAA.upper(), MD5_AAA[:-1], MD5_AAA + "0", 7, None])
def test_read_record_digest(path_tmp, value):
    """A digest in uppercase would never match the one of Zenodo, so it is refused."""
    record = json.dumps({"md5": value, "path": "a.txt", "size": 4})
    path = write_inventory_text(path_tmp, MD5_HEADER + record + "\n")
    with pytest.raises(ValueError, match="does not have 32 lowercase hexadecimal digits"):
        read_records(path)


@pytest.mark.parametrize("value", [-1, 4.0, "4", True, None])
def test_read_record_size(path_tmp, value):
    record = json.dumps({"md5": MD5_AAA, "path": "a.txt", "size": value})
    path = write_inventory_text(path_tmp, MD5_HEADER + record + "\n")
    with pytest.raises(ValueError, match="the size on line 2 is not a non-negative int"):
        read_records(path)


@pytest.mark.parametrize("value", ["-rw-r--r--", "rw-r--r-", "abcdefghi", 420, None])
def test_read_record_mode(path_tmp, value):
    header = MD5_HEADER.replace('"md5",', '"md5","mode",')
    record = json.dumps({"md5": MD5_AAA, "mode": value, "path": "a.txt", "size": 4})
    path = write_inventory_text(path_tmp, header + record + "\n")
    with pytest.raises(ValueError, match="the mode on line 2 does not have the form rw-r--r--"):
        read_records(path)


def test_read_record_line_number(path_tmp):
    good = json.dumps({"md5": MD5_AAA, "path": "a.txt", "size": 4})
    bad = json.dumps({"md5": "x", "path": "b.txt", "size": 4})
    path = write_inventory_text(path_tmp, MD5_HEADER + good + "\n" + bad + "\n")
    with open_inventory(path) as reader:
        records = iter(reader)
        assert next(records) == FileRecord("a.txt", MD5_AAA, 4)
        with pytest.raises(ValueError, match="digest on line 3 does not have"):
            next(records)


def test_read_duplicate_path(path_tmp):
    record = json.dumps({"md5": MD5_AAA, "path": "a.txt", "size": 4})
    path = write_inventory_text(path_tmp, MD5_HEADER + record + "\n" + record + "\n")
    with pytest.raises(ValueError, match=r"line 3 repeats the path 'a\.txt'"):
        read_records(path)


def test_read_missing_newline(path_tmp):
    record = json.dumps({"md5": MD5_AAA, "path": "a.txt", "size": 4})
    path = write_inventory_text(path_tmp, MD5_HEADER + record)
    with pytest.raises(ValueError, match="line 2 does not end with a newline"):
        read_records(path)


def test_read_blank_line(path_tmp):
    path = write_inventory_text(path_tmp, MD5_HEADER + "\n")
    with pytest.raises(ValueError, match="line 2 is not valid JSON"):
        read_records(path)


def test_mask_inventory_modes():
    assert mask_inventory_modes(MODE_INVENTORY) == MODE_INVENTORY.replace(
        '"rw-r--r--"', '"*********"'
    )
