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
"""Synchronization of local datasets with drafst on Zenodo.

This script synchronizes your local version of a dataset
with the (draft of) this dataset on Zenodo.
This simplifies your interaction with Zenodo to the following steps:

1. Prepare a personal token
2. Write metadata in a configuration YAML file.
3. Include this script in your workflow to automatically sync data.
4. Publish the dataset through the Zenodo web interface.

After publication, only metadata can be updated, not the actual files.
If you need to upload different files, increment the version number.
This will result in a new draft that you can publish when it is final.

This script offers a simplified interface to Zenodo.
It does not try to mirror all of Zenodo's REST API features.
Zenodo has subtle differences in APIs for drafts and submitted records,
which are normalized in the `ZenodoWrapper` class to become identical.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from typing import Any

import attrs
import cattrs
import requests
import semver
import yaml
from markdown_it import MarkdownIt
from path import Path

from stepup.core.api import amend


class RESTError(Exception):
    """Raised when a REST API call is not successful."""


class ZenodoError(Exception):
    """Raised in case of an error in the logic of the main script."""


@attrs.define
class RESTWrapper:
    """Wrapper for REST APIs that use JSON input (mostly) and output (always)."""

    endpoint: str = attrs.field()
    params: dict[str, str] = attrs.field()
    verbose: bool = attrs.field(default=False)

    def request(self, method: str, loc: str, **kwargs) -> Any:
        """Send a HTTP request and deserialize the response as JSON.

        Parameters
        ----------
        method
            The HTTP method: GET, POST, PUT or DELETE.
        loc
            The address to be appended after the endpoint.
        kwargs
            Keyword arguments to pass on to the `requests.request` function.

        Returns
        -------
        response_data
            Deserialized JSON response data.
        """
        url = f"{self.endpoint}/{loc}"
        if self.verbose:
            print(f"{method} {url}")
        res = requests.request(method, url, params=self.params, **kwargs)
        data = None if len(res.text) == 0 else res.json()
        if not res.ok:
            raise RESTError(
                f"Failed {method} {url}: {res.status_code}\n" + json.dumps(data, indent=2)
            )
        if self.verbose:
            print(json.dumps(data, indent=2))
        return data

    def get(self, loc: str, **kwargs):
        """Create a GET HTTP requests. See `request` method for details."""
        return self.request("GET", loc, **kwargs)

    def post(self, loc: str, **kwargs):
        """Create a POST HTTP requests. See `request` method for details."""
        return self.request("POST", loc, **kwargs)

    def put(self, loc: str, **kwargs):
        """Create a PUT HTTP requests. See `request` method for details."""
        return self.request("PUT", loc, **kwargs)

    def delete(self, loc: str, **kwargs):
        """Create a DELETE HTTP requests. See `request` method for details."""
        return self.request("DELETE", loc, **kwargs)


ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", re.IGNORECASE)


@attrs.define
class Creator:
    """A Zenodo creator"""

    name: str = attrs.field(converter=str.strip)
    """Formatted as `last, first`."""

    affiliation: str = attrs.field(converter=str.strip)
    """The affiliation of the creator, e.g. a university or research institute."""

    orcid: str | None = attrs.field(
        converter=(lambda s: None if s is None else s.strip()),
        default=None,
    )
    """The ORCID of the creator."""

    @orcid.validator
    def _validate_orcid(self, _attribute, value):
        """Validate the ORCID."""
        if value is None:
            return
        if len(value) != 19:
            raise ValueError("The ORCID must be 19 characters long, including the hyphens.")
        if not ORCID_PATTERN.match(value):
            raise ValueError(
                "The ORCID must be formatted as `0000-0000-0000-0000` "
                "(4 digits, hyphen, 4 digits, hyphen, 4 digits, hyphen, 3 digits or X)."
            )
        total = 0
        for char in value[:-1].replace("-", ""):
            total = (total + int(char)) * 2
        checksum = (12 - (total % 11)) % 11
        if checksum == 10 and value[-1].upper() != "X":
            raise ValueError("ORCID checksum failed, please check for typos.")
        if checksum != 10 and value[-1] != str(checksum):
            raise ValueError("ORCID checksum failed, please check for typos.")


@attrs.define
class Metadata:
    """A subset of the Zenodo metadata."""

    title: str = attrs.field(validator=attrs.validators.min_len(1))
    version: str = attrs.field(converter=str.strip)
    license: str = attrs.field(converter=lambda s: s.strip().lower())
    upload_type: str = attrs.field(
        validator=attrs.validators.in_(
            [
                "publication",
                "poster",
                "presentation",
                "dataset",
                "image",
                "video",
                "software",
                "lesson",
                "physicalobject",
                "other",
            ]
        )
    )
    creators: list[Creator] = attrs.field()
    description: str | None = attrs.field(default=None)


@attrs.define
class File:
    """A subset of the Zenodo file."""

    version_id: str = attrs.field()
    name: str = attrs.field()
    size: int = attrs.field()
    checksum: str = attrs.field()
    links: dict[str, str] = attrs.field()


@attrs.define
class Record:
    """A subset of the Zenodo record API.

    For a full definition, see:
    https://github.com/zenodo/zenodo/tree/master/zenodo/modules/deposit/jsonschemas/deposits/records
    """

    record_id: int | None = attrs.field()
    metadata: Metadata = attrs.field()
    links: dict[str, str] = attrs.field()
    files: list[File] = attrs.field()
    state: str = attrs.field()
    submitted: bool = attrs.field()


@attrs.define
class ZenodoWrapper:
    """Python interface to a subset of the Zenodo API."""

    token: str = attrs.field()
    endpoint: str = attrs.field(default="https://sandbox.zenodo.org/api")
    verbose: bool = attrs.field(default=False)
    rest: RESTWrapper = attrs.field(init=False)

    @rest.default
    def _default_rest(self):
        """Set the default RESP Wrapper."""
        return RESTWrapper(self.endpoint, {"access_token": self.token}, verbose=self.verbose)

    def create_new_record(self, metadata: Metadata) -> Record:
        """Create a new record on Zenodo, which remains in draft until it is published manually."""
        data = {"metadata": self._unstructure_metadata(metadata)}
        res = self.rest.post("deposit/depositions", json=data)
        self._normalize_record(res)
        return cattrs.structure(res, Record)

    def get_record(self, record_id: int) -> Record:
        """Get an (un)published record with given id.

        Note that Zenodo has different APIs for submitted and draft records.
        This method tries both and normalizes the record so that the caller
        does not have to deal with those differences.
        """
        try:
            # If the dataset is in draft
            res = self.rest.get(f"deposit/depositions/{record_id}")
        except RESTError:
            # If the dataset is published
            res = self.rest.get(f"records/{record_id}")
        self._normalize_record(res)
        return cattrs.structure(res, Record)

    def update_record(self, record_id: int, metadata: Metadata) -> Record:
        """Update the metadata of a record.

        This is applicable draft records and published records in edit mode.
        """
        data = {"metadata": self._unstructure_metadata(metadata)}
        data["metadata"]["publication_date"] = date.today().isoformat()
        res = self.rest.put(f"deposit/depositions/{record_id}", json=data)
        self._normalize_record(res)
        return cattrs.structure(res, Record)

    def edit_record(self, record_id: int):
        """Put a published record into edit mode."""
        self.rest.post(f"deposit/depositions/{record_id}/actions/edit")

    def publish_record(self, record_id: int):
        """Publish are draft record or a record in edit mode."""
        self.rest.post(f"deposit/depositions/{record_id}/actions/publish")

    def upload_file(self, bucket: str, path: str, name: str) -> File:
        """Upload a file. The buckect must belong to a record in draft mode."""
        with open(path, "rb") as fh:
            res = self.rest.put(f"{bucket}/{name}", data=fh)
        # Normalize file info before structuring.
        res["checksum"] = res["checksum"][4:]
        res["name"] = res["key"]
        self._normalize_links(res["links"])
        return cattrs.structure(res, File)

    def delete_file(self, record_id: int, file_id: str):
        """Delete a file. The file must belong to a record in draft mode."""
        self.rest.delete(f"deposit/depositions/{record_id}/files/{file_id}")

    def create_new_version(self, record_id: int) -> Record:
        """Create a new version of a published record. The result is a draft record."""
        res = self.rest.post(f"deposit/depositions/{record_id}/actions/newversion")
        self._normalize_record(res)
        return cattrs.structure(res, Record)

    def _unstructure_metadata(self, metadata: Metadata) -> dict[str]:
        """Turn a Metadata instance into a JSON-able dictionary."""
        result = cattrs.unstructure(metadata)
        self._normalize_metadata(result)
        return result

    def _normalize_record(self, record: dict[str]):
        """Normalize a record received from Zenodo."""
        if "id" in record and "record_id" not in record:
            record["record_id"] = record["id"]
        self._normalize_links(record.get("links"))
        self._normalize_metadata(record.get("metadata"))
        for file in record.get("files", []):
            self._normalize_file(file)

    def _normalize_file(self, file: dict[str]):
        """Normalize a file received from Zenodo."""
        file["version_id"] = file["id"]
        if "checksum" in file and file["checksum"].startswith("md5:"):
            file["checksum"] = file["checksum"][4:]
        if "size" not in file and "filesize" in file:
            file["size"] = file["filesize"]
        if "name" not in file:
            if "filename" in file:
                file["name"] = file["filename"]
            elif "key" in file:
                file["name"] = file["key"]
        self._normalize_links(file["links"])

    def _normalize_links(self, links: dict[str, str]):
        """Normalize the links received from Zenodo: remove non-API urls and remove endpoint."""
        for key, url in list(links.items()):
            if isinstance(url, str) and url.startswith(self.endpoint):
                links[key] = url[len(self.endpoint) + 1 :]
            else:
                del links[key]

    @staticmethod
    def _normalize_metadata(metadata: dict[str]):
        """Normalize metadata received from Zenodo or taken from the YAML config."""
        if metadata["description"] is None:
            del metadata["description"]
        if "upload_type" not in metadata and "resource_type" in metadata:
            metadata["upload_type"] = metadata["resource_type"]["type"]
        if isinstance(metadata["license"], dict) and "id" in metadata["license"]:
            metadata["license"] = metadata["license"]["id"]
        if "version" not in metadata:
            metadata["version"] = "TODO"
        for creator in metadata.get("creators", []):
            if "orcid" in creator and creator["orcid"] is None:
                del creator["orcid"]


@attrs.define
class Config:
    """Configuration datastructure.

    An object of this class is created from data loaded from a local YAML config file.
    It provides a more convenient way to access the configuration data.
    """

    path_versions: str = attrs.field()
    endpoint: str = attrs.field()
    path_token: str = attrs.field()
    metadata: Metadata = attrs.field()
    path_readme: str | None = attrs.field(default=None)
    paths: list[str] = attrs.field(factory=list)


def main(argv: list[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="rr-sync-zenodo",
        description="Synchronize a draft dataset on Zenodo with your local files.",
    )
    add_parser_args(parser)
    args = parser.parse_args(argv)
    sync_zenodo_tool(args)


def sync_zenodo_tool(args: argparse.Namespace) -> int:
    """Main program."""
    with open(args.config) as fh:
        data = yaml.safe_load(fh)
        if not isinstance(data.get("metadata").get("version"), str):
            raise TypeError(
                "The version in the YAML config file is missing or is not a string. "
                "Enclose the version in quotes to make it a string."
            )
        config = cattrs.structure(data, Config)
    update_online(config, args.verbose)
    return 0


def sync_zenodo_subcommand(subparser: argparse.ArgumentParser) -> callable:
    """Create parser for command-line options."""
    parser = subparser.add_parser(
        "sync-zenodo",
        help="Synchronize a draft dataset on Zenodo with your local files.",
    )
    add_parser_args(parser)
    return sync_zenodo_tool


def add_parser_args(parser: argparse.ArgumentParser):
    """Define command-line arguments."""
    parser.add_argument("config", help="Configuration YAML file.")
    parser.add_argument(
        "--verbose",
        "-v",
        default=False,
        action="store_true",
        help="Show details of communication with Zenodo endpoint.",
    )


def load_version(path_versions: str, version: str) -> int:
    """Load the record_id for a given version from a versions.json file."""
    path_versions = Path(path_versions)
    if not path_versions.is_file():
        return None
    with open(path_versions) as fh:
        versions = json.load(fh)
    if len(versions) == 0:
        return None
    record_id = versions.get(version)
    if record_id is not None:
        return record_id
    return max(versions.values())


def dump_version(path_versions: str, version: str, record_id: int):
    """Dump the record_id for a given version into a versions.json file."""
    path_versions = Path(path_versions)
    if not path_versions.is_file():
        versions = {}
    else:
        with open(path_versions) as fh:
            versions = json.load(fh)
    versions[version] = record_id
    # Serialize before opening file,
    # so no information is lost when JSON fails.
    serialized = json.dumps(versions, indent=2)
    with open(path_versions, "w") as fh:
        fh.write(serialized)
        fh.write("\n")


def update_online(config: Config, verbose: bool):
    """Make the online data set up to date with the local information."""
    # Amend inputs when this script is called in a StepUp workflow.
    paths_inp = list(config.paths)
    if config.path_readme is not None:
        paths_inp.append(config.path_readme)
    amend(inp=paths_inp)

    # If present, convert README Markdown file to HTML
    if config.path_readme is not None:
        if not config.path_readme.endswith(".md"):
            raise ValueError("The README Markdown file must end with the .md extension.")
        md = MarkdownIt()
        with open(config.path_readme) as fh:
            config.metadata.description = md.render(fh.read())

    # Run sanity check on paths: duplicate filenames not allowed.
    paths = {}
    for path in config.paths:
        path = Path(path)
        paths[path.name] = path
    if len(paths) != len(config.paths):
        raise ZenodoError(
            "Zenodo does not support directory layouts. Files must have a different names."
        )

    # (Try to) get the token.
    path_token = Path(config.path_token).expand()
    if not path_token.is_file():
        return
    with open(path_token) as fh:
        zenodo = ZenodoWrapper(fh.read().strip(), config.endpoint, verbose=verbose)

    # Interact with Zenodo.
    record_id = load_version(config.path_versions, config.metadata.version)
    if record_id is None:
        # New record, when getting started with a dataset.
        record = _create_new(zenodo, config.metadata, paths, config.metadata.version)
        dump_version(config.path_versions, config.metadata.version, record.record_id)
    else:
        # When a dataset exists, the actions depend on the current status of the record.
        record = zenodo.get_record(record_id)
        if record.submitted:
            cmpver = semver.compare(config.metadata.version, record.metadata.version)
            if cmpver == 0:
                _check_record_md5(record, paths, config.metadata.version)
                if record.metadata != config.metadata:
                    _republish_metadata(zenodo, record_id, config.metadata)
            elif cmpver > 0:
                record = _create_new_version(zenodo, record_id, config.metadata)
                dump_version(config.path_versions, config.metadata.version, record.record_id)
                _refresh_files(zenodo, record, paths, config.metadata.version)
            else:
                raise ZenodoError(
                    f"The online version ({record.metadata.version}) is newer "
                    f"than the local one ({config.metadata.version})."
                )
        else:
            changed = _refresh_files(zenodo, record, paths, config.metadata.version)
            if changed or record.metadata != config.metadata:
                zenodo.update_record(record_id, config.metadata)


def _create_new(
    zenodo: ZenodoWrapper, metadata: Metadata, paths: dict[str, Path], version: str
) -> Record:
    """Create a new record on Zenodo."""
    record = zenodo.create_new_record(metadata)
    for name, path in paths.items():
        print(f"Uploading {path}")
        file = zenodo.upload_file(record.links["bucket"], path, name)
        if not _match_md5(path, file.checksum):
            raise ZenodoError(f"MD5 Checksum mismatch for {path} ({version}, new)")
    return record


def _match_md5(path: str, checksum: str) -> bool:
    """Compute the MD5 sum of a file and compare to the given checksum."""
    with open(path, "rb") as fh:
        return checksum == hashlib.file_digest(fh, hashlib.md5).hexdigest()


def _check_record_md5(record: Record, paths: dict[str, Path], version: str):
    """Sanity check of MD5 hashes received from Zenodo"""
    for file in record.files:
        if file.name not in paths:
            raise ZenodoError(
                f"File {file.name} exists online but not locally ({version}, published)"
            )
        path = paths[file.name]
        if not _match_md5(path, file.checksum):
            raise ValueError(f"MD5 Checksum mismatch for {path} ({version}, published)")
    online_names = {file.name for file in record.files}
    for name in paths:
        if name not in online_names:
            raise OSError(f"File {name} exists locally but not online ({version}, published)")


def _republish_metadata(zenodo: ZenodoWrapper, record_id: int, metadata: Metadata):
    """Put a record in edit mode, update the metadata and publish again."""
    print(f"Editing metadata and publishing same version ({metadata.version}) again.")
    zenodo.edit_record(record_id)
    zenodo.update_record(record_id, metadata)
    zenodo.publish_record(record_id)


def _create_new_version(zenodo: ZenodoWrapper, record_id: int, metadata: Metadata) -> Record:
    """Create a new version of the dataset and refresh the metadata."""
    print(f"Creating a new version ({metadata.version})")
    record = zenodo.create_new_version(record_id)
    return zenodo.update_record(record.record_id, metadata)


def _refresh_files(
    zenodo: ZenodoWrapper, record: Record, paths: dict[str, Path], version: str
) -> bool:
    """Refresh the online files.

    This function only uploads files that do not exist online yet or have changed locally.
    Files removed from the local YAML config will also be removed online.
    """
    changed = False
    for file in record.files:
        if file.name not in paths:
            print(f"Deleting {file.name} ({version}, draft)")
            zenodo.delete_file(record.record_id, file.version_id)
            changed = True
        else:
            path = paths[file.name]
            if not _match_md5(path, file.checksum):
                print(f"Replacing {path} ({version}, draft)")
                zenodo.delete_file(record.record_id, file.version_id)
                file = zenodo.upload_file(record.links["bucket"], path, file.name)
                if not _match_md5(path, file.checksum):
                    raise ZenodoError(f"MD5 Checksum mismatch for {path} ({version}, draft)")
                changed = True
    online_names = {file.name for file in record.files}
    for name, path in paths.items():
        if name not in online_names:
            print(f"Uploading {path} ({version}, draft)")
            file = zenodo.upload_file(record.links["bucket"], path, name)
            if not _match_md5(path, file.checksum):
                raise ZenodoError(f"MD5 Checksum mismatch for {path} ({version}, draft)")
            changed = True
    return changed


if __name__ == "__main__":
    main(sys.argv[1:])
