# MANIFEST files

`MANIFEST.txt` files are used in StepUp RepRep to prepare a ZIP archive.
Such manifests can either be created manually (for an external dataset) or automatically (for datasets created within a StepUp workflow.)


## File Formats

### `MANIFEST.txt`

The `MANIFEST.txt` file contains one line per file to be archived.
Each line has three values:

- the file size,
- the [BLAKE2b](https://en.wikipedia.org/wiki/BLAKE_(hash_function)#BLAKE2) hash of the file, and
- the relative path of the file.

A fixed column width is used.
You do not create this type of file manually.
Instead, StepUp RepRep offers several tools to make such files.
(See below.)


### `MANIFEST.in`

The `MANIFEST.in` file format is borrowed from the [setuptools](https://setuptools.pypa.io/) project.
Documentation of this format can be found [here](https://setuptools.pypa.io/en/latest/userguide/miscellaneous.html#using-manifest-in).


## Creating `MANIFEST.txt` Files.

### Command-line Tool `reprep-make-manifest`

One may create manifest files with the command-line tool as follows:

```bash
reprep-make-manifest -i MANIFEST.in -o MANIFEST.txt
```

See `reprep-make-manifest --help` for more details.
This tool is suitable for creating manifest files of external datasets.

### StepUp RepRep Function `make_manifest`

One may include a [`make_manifest()`][stepup.reprep.api.make_manifest] step in `plan.py` as follows:

```python
from stepup.reprep.api import make_manifest

# Option 1: use a MANIFEST.in file
make_manifest("MANIFEST.in")
# Option 2: list all files explicitly
make_manifest("MANIFEST.txt", ["file1.txt", "file2.txt", ...])
```

Such steps are mainly useful for creating manifests of datasets generated in the StepUp workflow.


## Creating a ZIP Archive From a `MANIFEST.txt` File

The function [`zip_manifest()`][stepup.reprep.api.zip_manifest] takes a `MANIFEST.txt` file as input and creates a ZIP file containing all the files listed in the manifest.
It differs from the conventional `zip` program in the following ways:

- File hashes are checked before adding files to the archive,
  which is mostly useful for external datasets.
- The manifest is included in the resulting ZIP file.
- The ZIP file is reproducible: all time stamps in the ZIP file are set to January 1st, 1980.
