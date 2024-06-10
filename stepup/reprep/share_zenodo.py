# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# Copyright (C) 2024 Toon Verstraelen
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
"""Online sharing and archiving on Zenodo."""

import argparse
import hashlib
import json
import sys

import attrs
import cattrs
import markdown
import requests
import semver
import yaml
from path import Path

from stepup.core.api import amend


class RESTError(Exception):
    """Raised when a REST API call is not successful."""


class VersionError(ValueError):
    """Raised when the online version is newer than the local one"""


@attrs.define
class RESTWrapper:
    """Wrapper for REST APIs that use JSON input (mostly) and output (always)."""

    endpoint: str = attrs.field()
    params: dict[str, str] = attrs.field()
    verbose: bool = attrs.field(default=False)

    @property
    def params(self) -> dict[str, str]:
        raise NotImplementedError

    def request(self, method, loc, **kwargs):
        url = f"{self.end_point}/{loc}"
        if self.verbose:
            print(f"{method} {url}")
        res = requests.request(method, url, params=self.params, **kwargs)
        data = res.json()
        if not res.ok:
            raise RESTError(
                f"Failed {method} {url}: {res.status_code}\n" + json.dumps(data, indent=2)
            )
        if self.verbose:
            print(json.dumps(data, indent=2))
        return data

    def get(self, loc, **kwargs):
        return self.request("GET", loc, **kwargs)

    def post(self, loc, **kwargs):
        return self.request("POST", loc, **kwargs)

    def put(self, loc, **kwargs):
        return self.request("PUT", loc, **kwargs)

    def delete(self, loc, **kwargs):
        return self.request("DELETE", loc, **kwargs)


@attrs.define
class Creator:
    """A Zenodo creator"""

    name: str = attrs.field()
    """Formatted as `last, first`."""

    affiliation: str = attrs.field()


@attrs.define
class Metadata:
    """A subset of the Zenodo metadata."""

    title: str = attrs.field(validator=attrs.validators.min_len(1))
    # TODO: do not interpret float when loading yaml.
    version: str = attrs.field(converter=semver.Version.parse)
    license: str = attrs.field()
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
    doi_url: str = attrs.field()
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
    rest: RESTWrapper = attrs.field(init=False)

    @rest.default
    def _default_resp(self):
        return RESTWrapper(self.endpoint, {"access_token": self.token})

    def create_new_record(self, metadata: Metadata) -> Record:
        data = {"metadata": self._unstructure_metadata(metadata)}
        res = self.rest.post("deposit/depositions", json=data)
        return cattrs.structure(res, Record)

    def update_record(self, record_id: int, metadata: Metadata) -> Record:
        data = {"metadata": self._unstructure_metadata(metadata)}
        res = self.rest.put(f"deposit/depositions/{record_id}", json=data)
        return cattrs.structure(res, Record)

    def upload_file(self, bucket_loc: str, path: str, name: str) -> File:
        with open(path, "rb") as fh:
            res = self.rest.put(f"{bucket_loc}/{name}", data=fh)
        # Normalize file info before structuring.
        res["checksum"] = res["checksum"][4:]
        res["name"] = res["key"]
        self._normalize_links(res["links"])
        return cattrs.structure(res, File)

    def delete_file(self, record_id: int, file_id: str):
        self.rest.delete(f"deposit/depositions/{record_id}/files/{file_id}")

    def create_new_version(self, record_id: int) -> Record:
        res = self.rest.post(f"deposit/depositions/{record_id}/actions/newversion")
        return cattrs.structure(res, Record)

    @staticmethod
    def _unstructure_metadata(metadata: Metadata) -> dict[str]:
        result = cattrs.unstructure(metadata)
        if result["description"] is None:
            del result["description"]
        return result

    def _normalize_record(self, record: dict):
        """Normalize the returned record received from Zenodo.

        The file id is the version_id. (?)
        """
        for file_dict in record.get("files", []):
            file_dict["version_id"] = file_dict["id"]
            file_dict["size"] = file_dict["filesize"]
            file_dict["name"] = file_dict["filename"]
            self._normalize_links(file_dict["links"])

    def _normalize_links(self, links: dict[str, str]):
        """Normalize the links: remove non-API urls and remove endpoint."""
        for key, url in list(links.items()):
            if not url.startswith(self.endpoint):
                del links[key]
            else:
                links[key] = url[len(self.endpoint) + 1 :]


@attrs.define
class Config:
    record_id: int | None = attrs.field()
    endpoint: str = attrs.field()
    path_token: str = attrs.field()
    metadata: Metadata = attrs.field()
    path_readme: str | None = attrs.field(default=None)
    paths: list[str] = attrs.field(factory=list)


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    with open(args.config) as fh:
        config = cattrs.structure(yaml.safe_load(fh), Config)
    update_online(config)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="reprep-share-zenodo", description="Sync a draft dataset on Zenodo."
    )
    parser.add_argument("config", help="Configuration YAML file.")
    return parser.parse_args(argv)


def update_online(config: Config):
    """Make the online data set up to date with the local information."""
    paths_inp = list(config.paths)
    if config.path_readme is not None:
        paths_inp.append(config.path_readme)
    if not amend(inp=paths_inp):
        return

    # If present, convert README Markdown file to HTML
    if config.path_readme is not None:
        if not config.path_readme.endswith(".md"):
            raise ValueError("The README Markdown file must end with the .md extension.")
        md_ctx = markdown.Markdown(extensions=["fenced_code"])
        with open(config.path_readme) as fh:
            config.metadata.description = md_ctx.convert(fh.read())

    # Run sanity check on paths: duplicate filenames not allowed.
    paths = {}
    for path in config.paths:
        path = Path(path)
        paths[path.name] = path
    if len(paths) != len(config.paths):
        raise OSError(
            "Zenodo does not support directory layouts. Files must have a different names."
        )

    # (Try to) get the token.
    path_token = Path(config.path_token).expand()
    if not path_token.is_file():
        return
    with open(path_token) as fh:
        zenodo = ZenodoWrapper(fh.read().strip(), config.endpoint)

    # Interact with Zenodo.
    if config.record_id is None:
        record = _create_new(zenodo, config.metadata, paths)
        print(f"Record ID to include in the config file: {record.id}")
    else:
        record = zenodo.update_record(config.record_id, config.metadata)
        if record.submitted:
            cmpver = semver.compare(config.metadata.version, record.metadata.version)
            if cmpver == 0:
                _check_record_md5(record, paths)
            elif cmpver > 0:
                record = _create_new_version(zenodo, config.record_id, config.metadata)
                _refresh_files(zenodo, record, paths)
            else:
                raise VersionError("The online dataset has a newer version than the local one.")
        else:
            _refresh_files(zenodo, record, paths)


def _create_new(zenodo: ZenodoWrapper, metadata: Metadata, paths: dict[str, Path]) -> Record:
    """Create a new record on Zenodo."""
    record = zenodo.create_new_record(metadata)
    for name, path in paths.items():
        file = zenodo.upload_file(record.links["bucket"], path, name)
        if not _match_md5(path, file.checksum):
            raise ValueError(f"MD5 Checksum mismatch for {path}")
    return record


def _match_md5(path: str, checksum: str) -> bool:
    with open(path, "rb") as fh:
        return checksum == hashlib.file_digest(fh, hashlib.md5).hexdigest()


def _check_record_md5(record: Record, paths: dict[str, Path]):
    """Sanity check of MD5 hashes received from Zenodo"""
    for file in record.files:
        if file.name not in paths:
            raise OSError(f"File {file.name} exists online but not locally.")
        path = paths[file.name]
        if not _match_md5(path, file.checksum):
            raise ValueError(f"MD5 Checksum mismatch for {path}")
    online_names = {file.name for file in record.files}
    for name in paths:
        if name not in online_names:
            raise OSError(f"File {name} exists locally but not online.")


def _create_new_version(zenodo: ZenodoWrapper, record_id: int, metadata: Metadata) -> Record:
    """Create a new version of the dataset and refresh the metadata."""
    zenodo.create_new_version(record_id)
    return zenodo.update_record(record_id, metadata)


def _refresh_files(zenodo: ZenodoWrapper, record: Record, paths: dict[str, Path]):
    """Update the online files, only uploading files that do not exit yet online or have changed."""
    for file in record.files:
        if file.name not in paths:
            zenodo.delete_file(record.record_id, file.version_id)
        path = paths[file.name]
        if not _match_md5(path, file.checksum):
            zenodo.delete_file(record.record_id, file.version_id)
            zenodo.upload_file(record.links["bucket"], path, file.name)
    online_names = {file.name for file in record.files}
    for name, path in paths.items():
        if name not in online_names:
            zenodo.upload_file(record.links["bucket"], path, name)


if __name__ == "__main__":
    main(sys.argv[1:])
