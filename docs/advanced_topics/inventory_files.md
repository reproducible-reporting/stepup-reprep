---
description: >-
  The inventory.jsonl and inventory.def file formats,
  and the tools that create, validate and zip an inventory of files to be archived.
---

<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Inventory Files

An inventory lists files together with their sizes and digests.
StepUp RepRep uses inventories to prepare reproducible ZIP archives,
to check the integrity of a dataset, and to upload files to Zenodo with
[`sync_zenodo()`](sync_zenodo.md).
Inventory files can either be created for an external dataset
or within a StepUp workflow, for a dataset that the workflow builds.

## File Formats

### Inventory Files (`inventory.jsonl`)

An inventory is a [JSON Lines](https://jsonlines.org/) file
with one JSON object per line, encoded in UTF-8.
You do not write this type of file by hand.
Instead, StepUp RepRep offers tools to make such files, see below.
The following example lists a regular file and a symbolic link:

```json
{"fields":["md5","path","size"],"format":"stepup-reprep-inventory","version":1}
{"md5":"b1946ac92492d2347c6235b4d2611184","path":"README.txt","size":6}
{"link":"README.txt","path":"README.md"}
```

The first line is the header, with the following keys:

- `format` is always `"stepup-reprep-inventory"`,
  which tells an inventory apart from other JSON files.
- `version` is the version of the format, currently `1`.
  It changes with every incompatible change of the format.
- `fields` is the sorted list of keys of the line of a regular file.

Every other line describes one file.
For a regular file, the keys are exactly those listed in `fields`:

- `path` is the location of the file, see below.
- `size` is the size of the file in bytes.
- The digest of the file contents in lowercase hexadecimal digits,
  under the name of the hash algorithm, e.g. `md5` or `sha256`.
  All files in one inventory are hashed with the same algorithm.
- `mode` is only present when the inventory was made with `--mode`.
  It holds the permission bits of the file, e.g. `rw-r--r--`.

A symbolic link is never followed.
Its line has exactly two keys, whatever `fields` says:
`path` is the location of the link, and `link` is the target as stored in the link.

A path is relative to the parent directory of the inventory file,
it is normalized and it uses `/` as separator on every platform.
It may start with `../` for a file outside that directory.
Directories are never listed, and neither are symbolic links to directories,
because StepUp cannot track a directory as an input.
`srr-make-inventory` refuses them when they are given explicitly,
and leaves them out when an inventory definition matches them.

Files appear in the order in which they were given:
first the paths given explicitly, in the given order,
then the matches of the inventory definition, sorted.
When a path occurs twice, only its first occurrence is kept.
This order matters for [`sync_zenodo()`](sync_zenodo.md),
which selects the first file for the preview on Zenodo.

The contents of an inventory only depend on the files it lists.
It contains no time stamps, so StepUp does not rerun the steps that use it
when the files did not change.

### Inventory Definitions (`inventory.def`)

The `inventory.def` format is inspired by the `MANIFEST.in` format
from the [setuptools](https://setuptools.pypa.io/) project.
As of version 1.2.0, StepUp RepRep no longer relies on setuptools
and has its own implementation to process inventory definitions.

Inventory definition files are processed one line at a time.
Comments start with the `#` character, just as in Python source code.
Empty lines or lines containing only comments are ignored.
A Non-empty line must contain one command starting with `include` or `exclude`.
Each command first generates a new list of paths.
An `include` command will add the newly generated paths to the inventory,
whereas an `exclude` command will remove them from the inventory (if present).
Each command operates on the file list constructed by preceding commands.
(The first command starts from an empty list.)

The following rules are supported:

- A bare `include` or `exclude` is followed by one or more
  [Named Glob patterns](https://reproducible-reporting.github.io/stepup-core/reference/stepup.core.nglob/),
  which may also contain `**` wildcards to match files recursively.
- The `include-git` and `exclude-git` use `git ls-files` to generate a list of files.
  Arguments to this command are optional and are passed to `git ls-files`.
- The `include-workflow` and `exclude-workflow` extract a file list
  from one or more StepUp `graph.db` files.
  The first argument is the state of the files to be selected.
  (`CONFIRMED` or `BUILT` are common.
  Other states exist but make less sense.)
  All subsequent arguments are (Named Glob patterns matching) StepUp `graph.db` files.

If any of these rules produces directories, they will not be included in the inventory.
An exception is raised when no matching paths are found.

## Creating `inventory.jsonl` Files

### Command-Line Tool `srr-make-inventory`

One can create an inventory file on the command-line as follows:

```bash
srr-make-inventory -i inventory.def -o inventory.jsonl
```

The output must have the suffix `.jsonl`.
With `-i X.def` and without `-o`, the inventory is written to `X.jsonl`.
The inventory definition and the output must be in the same directory.
Files can also be listed on the command line, before the options,
with or without an inventory definition:

```bash
srr-make-inventory README.txt data/table.csv -o inventory.jsonl
```

See `srr-make-inventory --help` for more details.
This tool is suitable for creating inventory files of external datasets.

### StepUp RepRep Function `make_inventory`

One may include a [`make_inventory()`][stepup.reprep.api.make_inventory] step in `plan.py` as follows:

```python
from stepup.reprep.api import make_inventory

make_inventory("file1.txt", "file2.txt", "inventory.jsonl")
```

The last argument is the inventory file to write.
This step is mainly useful for creating an inventory file of a dataset generated by your StepUp workflow.
It can also be combined with `stepup.core.glob` for building datasets from static files,
or one may provide an inventory definition file as follows:

```python
from stepup.reprep.api import make_inventory

make_inventory("inventory.jsonl", path_def="inventory.def")
```

The options below are the arguments `hash_algorithm` and `mode` of `make_inventory()`.

### Hash Algorithm

The option `--hash` selects the hash algorithm for the digests of the files.
Any algorithm in Python's
[`hashlib.algorithms_guaranteed`](https://docs.python.org/3/library/hashlib.html#hashlib.algorithms_guaranteed)
can be used, except the `shake_*` algorithms, whose digests have no fixed length.

The default is MD5, because Zenodo reports MD5 checksums,
so an inventory with the default algorithm can be passed to [`sync_zenodo()`](sync_zenodo.md).
MD5 reliably detects accidental changes, such as a damaged transfer or bit rot,
because the chance of an accidental collision is negligible with MD5 as well as with SHA-256.
Use `--hash sha256` when deliberate tampering with the files must be detected,
because files with the same MD5 digest can be crafted on purpose.

### Permission Bits

The size and the digest of a regular file are always recorded.
The permission bits are only recorded with the option `--mode`,
e.g. to make sure that a script remains executable.
They are then also checked by `srr-check-inventory` and `srr-zip-inventory`.

Files have no permission bits on Windows,
where Python derives them from the read-only attribute and the file name.
`srr-make-inventory --mode` prints a warning on Windows,
and the permission bits in an inventory are not checked on Windows.

## Creating a ZIP Archive from an `inventory.jsonl` File

### Command-Line Tool `srr-zip-inventory`

Given an `inventory.jsonl` file, the corresponding ZIP file is created with:

```bash
srr-zip-inventory inventory.jsonl
```

This is a command-line wrapper around the `zip_inventory` function discussed below.

### StepUp RepRep Function `zip_inventory`

The function [`zip_inventory()`][stepup.reprep.api.zip_inventory]
takes an `inventory.jsonl` file as input
and creates a ZIP file containing all the files listed in the inventory.
It differs from the conventional `zip` program in the following ways:

- Every file is checked against the inventory before it is added to the archive,
  which is mostly useful for external datasets.
- The paths in the ZIP file are those in the inventory.
  A file outside the directory of the inventory, with a path starting with `../`,
  cannot be archived, so such an inventory is refused.
- The ZIP file is reproducible: all time stamps in the ZIP file are set to January 1st, 1980.
- Symbolic links are added as links, instead of the contents they point to.

For archival, keep the inventory as a separate file next to the ZIP file,
e.g. by uploading both to Zenodo,
so that the unpacked files can be checked with `srr-check-inventory`.

### Unpacking the ZIP File

To unpack the ZIP file, use the following command:

```bash
unzip inventory.zip
```

This will correctly handle symbolic links, unlike Python's built-in
[extractall](https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.extractall) method.
See [cpython#82102](https://github.com/python/cpython/issues/82102)
for more details on Python's (lacking) support for symbolic links in ZIP files.

The paths in the ZIP file are relative to the directory of the inventory.
Unpack the ZIP file in the directory that contains its inventory,
so that the unpacked files can be checked with `srr-check-inventory`, see below.

## Validate an Inventory File

If you just want to check the files listed in an inventory, run:

```bash
srr-check-inventory inventory.jsonl
```

This compares the size and the digest of every regular file,
its permission bits when the inventory has them,
and the target of every symbolic link.
This can be useful in the following cases:

- When you work with a remote dataset, you can check if the files in the inventory have changed.
- When you unpack a ZIP file created by `srr-zip-inventory` or `zip_inventory()`
  next to its inventory,
  you can check if the files are not affected by bit rot or other data integrity issues.
