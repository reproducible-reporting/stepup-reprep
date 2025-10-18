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
It does not try to mirror all of Zenodo's API features.

Note that the current version uses the Invenio RDM API (v12) to interact with Zenodo.
This API is not officially documented by Zenodo, but it is already used by Zenodo itself.
Relevant API documentation can be found here:

- https://inveniordm.docs.cern.ch/reference/rest_api_index/

Unofficial information on how to use the Invenio RDM API with Zenodo:

- https://github.com/zenodo/developers.zenodo.org/issues/62
- https://github.com/zenodo/zenodo/issues/2544

Note that the new Zenodo API (based on Invenio RDM) is still not fully stable.
Some of the features implemented in this module were deduced from the Zenodo web interface.
"""

import argparse
import datetime
import hashlib
import json
import sys
from typing import Any

import attrs
import cattrs
import idutils
import requests
import semver
import yaml
from markdown_it import MarkdownIt
from path import Path
from rich import print  # noqa: A004

from stepup.core.api import amend, getenv


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
            if "json" in kwargs:
                print("REQUEST")
                print(kwargs["json"])
        res = requests.request(method, url, params=self.params, **kwargs)
        data = None if len(res.text) == 0 else res.json()
        if not res.ok:
            raise RESTError(
                f"Failed {method} {url}: {res.status_code}\n" + json.dumps(data, indent=2)
            )
        if self.verbose:
            print("RESPONSE")
            print(data)
            print()
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


# See https://datacite-metadata-schema.readthedocs.io/en/4.6/properties/resourcetype/
RESOURCE_TYPES = [
    "audio",
    "dataset",
    "event",
    "image",
    "image-diagram",
    "image-drawing",
    "image-figure",
    "image-other",
    "image-photo",
    "image-plot",
    "lesson",
    "model",
    "other",
    "physicalobject",
    "poster",
    "presentation",
    "publication",
    "publication-annotationcollection",
    "publication-article",
    "publication-book",
    "publication-conferencepaper",
    "publication-conferenceproceeding",
    "publication-datamanagementplan",
    "publication-datapaper",
    "publication-deliverable",
    "publication-dissertation",
    "publication-journal",
    "publication-milestone",
    "publication-other",
    "publication-patent",
    "publication-peerreview",
    "publication-preprint",
    "publication-proposal",
    "publication-report",
    "publication-section",
    "publication-softwaredocumentation",
    "publication-standard",
    "publication-taxonomictreatment",
    "publication-technicalnote",
    "publication-thesis",
    "publication-workingpaper",
    "software",
    "software-computationalnotebook",
    "video",
    "workflow",
]

# See https://github.com/inveniosoftware/invenio-rdm-records/blob/master/invenio_rdm_records/config.py
IDENTIFIER_SCHEMES = {
    "ark": idutils.is_ark,
    "arxiv": idutils.is_arxiv,
    "ads": idutils.is_ads,
    "crossreffunderid": lambda _: True,
    "doi": idutils.is_doi,
    "ean13": idutils.is_ean13,
    "eissn": idutils.is_issn,
    "grid": lambda _: True,
    "handle": idutils.is_handle,
    "igsn": lambda _: True,
    "isbn": idutils.is_isbn,
    "isni": idutils.is_isni,
    "issn": idutils.is_issn,
    "istc": idutils.is_istc,
    "lissn": idutils.is_issn,
    "lsid": idutils.is_lsid,
    "pmid": idutils.is_pmid,
    "purl": idutils.is_purl,
    "upc": lambda _: True,
    "url": idutils.is_url,
    "urn": idutils.is_urn,
    "w3id": lambda _: True,
    "other": lambda _: True,
}

# See https://github.com/inveniosoftware/invenio-rdm-records/blob/master/invenio_rdm_records/fixtures/data/vocabularies/relation_types.yaml
RELATION_TYPES = [
    "cites",
    "compiles",
    "continues",
    "describes",
    "documents",
    "hasmetadata",
    "haspart",
    "hasversion",
    "iscitedby",
    "iscompiledby",
    "iscontinuedby",
    "isderivedfrom",
    "isdescribedby",
    "isdocumentedby",
    "isidenticalto",
    "ismetadatafor",
    "isnewversionof",
    "isobsoletedby",
    "isoriginalformof",
    "ispartof",
    "ispreviousversionof",
    "ispublishedin",
    "isreferencedby",
    "isrequiredby",
    "isreviewedby",
    "issourceof",
    "issupplementedby",
    "issupplementto",
    "isvariantformof",
    "isversionof",
    "obsoletes",
    "references",
    "requires",
    "reviews",
]


@attrs.define
class Organization:
    """A subset of Invenio RDM affiliation / funder."""

    name: str | None = attrs.field(default=None)
    """Name of the affiliation, e.g. a university or research institute."""

    ror: str | None = attrs.field(default=None)
    """The Research Organization Registry identifier."""

    @ror.validator
    def _validate_ror(self, attribute, value):
        """Validate the ROR identifiers."""
        if not (value is None or idutils.is_ror(value)):
            raise ValueError("Invalid ROR identifier format.")

    def __attrs_post_init__(self):
        if not ((self.name is None) ^ (self.ror is None)):
            raise ValueError("Exactly one of 'name' or 'ror' must be set for an affiliation.")

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the affiliation to a dictionary suitable for Zenodo."""
        result = {}
        if self.name is not None:
            result["name"] = self.name
        if self.ror is not None:
            result["id"] = self.ror
        if len(result) != 1:
            raise ValueError("Exactly one of 'name' or 'ror' must be set for an affiliation.")
        return result


@attrs.define
class Creator:
    """A subset of Invenio RDM creator."""

    family_name: str | None = attrs.field(default=None)
    """Family name."""

    given_name: str | None = attrs.field(default=None)
    """Given name."""

    identifiers: dict[str, str] = attrs.field(factory=dict)
    """Identifiers of the creator, e.g. ORCID or ISNI.

    Keys must be lower case strings.
    Values must not contain a https:// prefix, but only the identifier itself.
    For example, for ORCID, use '0000-0001-9288-5608'
    instead of 'https://orcid.org/0000-0001-9288-5608'.
    """

    @identifiers.validator
    def _validate_identifiers(self, attribute, value):
        """Validate the identifiers."""
        if not isinstance(value, dict):
            raise TypeError("Identifiers must be a dictionary.")
        for key in value:
            if key not in ["orcid", "isni"]:
                raise ValueError(
                    f"Unknown identifier type: {key}. Only 'orcid' or 'isni' are allowed."
                )
        if "orcid" in value:
            if not idutils.is_orcid(value["orcid"]):
                raise ValueError(f"Invalid ORCID: {value['orcid']}")
            if value["orcid"].startswith("http"):
                raise ValueError(
                    "ORCID identifiers must not start with 'http'. "
                    "Use only the identifier itself, e.g. '0000-0001-9288-5608'."
                )
        if "isni" in value:
            if not idutils.is_isni(value["isni"]):
                raise ValueError(f"Invalid ISNI: {value['isni']}")
            if value["isni"].startswith("http"):
                raise ValueError(
                    "ISNI identifiers must not start with 'http'. "
                    "Use only the identifier itself, e.g. '0000 0001 6785 333X'."
                )

    affiliations: list[Organization] = attrs.field(factory=list)
    """The affiliation of the creator, e.g. a university or research institute."""

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the creator to a dictionary suitable for Zenodo."""
        result = {
            "person_or_org": {
                "type": "personal",
                "family_name": self.family_name,
                "given_name": self.given_name,
            }
        }
        if len(self.identifiers) > 0:
            result["person_or_org"]["identifiers"] = [
                {"scheme": key, "identifier": value} for key, value in self.identifiers.items()
            ]
        if len(self.affiliations) > 0:
            result["affiliations"] = [aff.to_zenodo() for aff in self.affiliations]
        return result


@attrs.define
class Access:
    """A subset of Invenio RDM Access.

    https://inveniordm.docs.cern.ch/reference/metadata/#access
    """

    record: str = attrs.field(
        default="public",
        validator=attrs.validators.in_(["public", "restricted"]),
    )
    """The access level of the record. Public means that the record is visible to everyone."""

    files: str = attrs.field(
        default="public",
        validator=attrs.validators.in_(["public", "restricted"]),
    )
    """The access level of the files. Public means that the files are visible to everyone."""

    def to_zenodo(self) -> dict[str, str]:
        """Convert the access configuration to a dictionary suitable for Zenodo."""
        return {
            "record": self.record,
            "files": self.files,
        }


@attrs.define
class Related:
    scheme: str = attrs.field(validator=attrs.validators.in_(IDENTIFIER_SCHEMES))
    """The scheme of the identifier, e.g. 'doi', 'arxiv'"""

    identifier: str = attrs.field()
    """The identifier itself, e.g. '10.5281/zenodo.1234567'"""

    @identifier.validator
    def _validate_identifier(self, attribute, value):
        """Validate the identifier."""
        if not IDENTIFIER_SCHEMES[self.scheme](value):
            raise ValueError(
                f"Invalid identifier for scheme {self.scheme}: {value}. "
                "Please check the identifier format."
            )

    relation_type: str = attrs.field(validator=attrs.validators.in_(RELATION_TYPES))

    resource_type: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.in_(RESOURCE_TYPES)),
    )

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the related identifier to a dictionary suitable for Zenodo."""
        result = {
            "scheme": self.scheme,
            "identifier": self.identifier,
            "relation_type": {"id": self.relation_type},
        }
        if self.resource_type is not None:
            result["resource_type"] = {"id": self.resource_type}
        return result


@attrs.define
class Award:
    """A subset of Invenio RDM award information."""

    id: str | None = attrs.field(default=None)
    """The award ID, e.g. '123456'."""

    title: str | None = attrs.field(default=None)
    """The title of the award, e.g. 'Research Excellence Award'."""

    number: str | None = attrs.field(default=None)
    """The award number, e.g. 'RE-123456'."""

    identifiers: list[dict[str, str]] = attrs.field(
        factory=list,
    )
    """Identifiers of the award, e.g. a DOI or a funder ID. Keys must be lower case strings."""

    @identifiers.validator
    def _validate_identifiers(self, attribute, value):
        """Validate the identifiers."""
        if not isinstance(value, list):
            raise TypeError("Identifiers must be a list of dictionaries.")
        for item in value:
            if not isinstance(item, dict):
                raise TypeError("Each identifier must be a dictionary.")
            if len(item) != 1:
                raise ValueError("Each identifier must have exactly one key.")
            scheme, identifier = next(iter(item.items()))
            if scheme not in IDENTIFIER_SCHEMES:
                raise ValueError(f"Unknown identifier scheme: {scheme}")
            if not IDENTIFIER_SCHEMES[scheme](identifier):
                raise ValueError(f"Invalid identifier for scheme {scheme}: {identifier}")

    def __attrs_post_init__(self):
        if not ((self.id is None) ^ (self.title is None and self.number is None)):
            raise ValueError("Exactly one of 'id' or ('title', 'number') must be set for an award.")

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the award information to a dictionary suitable for Zenodo."""
        result = {}
        if self.id is not None:
            result["id"] = self.id
        if self.title is not None:
            result["title"] = {"en": self.title}
        if self.number is not None:
            result["number"] = self.number
        if len(self.identifiers) > 0:
            result["identifiers"] = []
            for item in self.identifiers:
                if not isinstance(item, dict) or len(item) != 1:
                    raise ValueError("Each identifier must be a dictionary with exactly one key.")
                scheme, identifier = next(iter(item.items()))
                result["identifiers"].append({"scheme": scheme, "identifier": identifier})
        return result


@attrs.define
class Funding:
    """A subset of Invenio RDM funding information."""

    funder: Organization = attrs.field()
    """The funder of the project leading to the record, e.g. a research council or a foundation."""

    award: Award = attrs.field()
    """The award associated with the funding, if any."""

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the funding information to a dictionary suitable for Zenodo."""
        return {
            "funder": self.funder.to_zenodo(),
            "award": self.award.to_zenodo(),
        }


def _convert_license(arg):
    if isinstance(arg, str):
        arg = [arg]
    return [lic.lower() for lic in arg]


@attrs.define
class Metadata:
    """A subset of Invenio RDM metadata.

    https://inveniordm.docs.cern.ch/reference/metadata/#metadata
    """

    title: str = attrs.field(validator=attrs.validators.min_len(1))
    version: str = attrs.field()
    license: str | list[str] = attrs.field(converter=_convert_license)
    resource_type: str = attrs.field(validator=attrs.validators.in_(RESOURCE_TYPES))
    copyright: str | None = attrs.field(default=None)
    publisher: str | None = attrs.field(default=None)
    keywords: list[str] = attrs.field(factory=list)
    creators: list[Creator] = attrs.field(factory=list)
    description: str | None = attrs.field(default=None)
    related: list[Related] = attrs.field(factory=list)
    funding: list[Funding] = attrs.field(factory=list)

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the metadata to a dictionary suitable for Zenodo."""
        data = {
            "title": self.title,
            "version": self.version,
            "rights": [{"id": lic} for lic in self.license],
            "resource_type": {"id": self.resource_type},
            "creators": [creator.to_zenodo() for creator in self.creators],
            "description": self.description,
            "publication_date": datetime.date.today().isoformat(),
            "related_identifiers": [rel.to_zenodo() for rel in self.related],
            "funding": [fund.to_zenodo() for fund in self.funding],
        }
        if self.copyright is not None:
            data["copyright"] = self.copyright
        if self.publisher is not None:
            data["publisher"] = self.publisher
        if len(self.keywords) > 0:
            data["subjects"] = [{"subject": keyword} for keyword in self.keywords]
        return data


@attrs.define
class Config:
    """Configuration of the sync-zenodo script.

    An object of this class is created from data loaded from a local YAML config file.
    """

    path_record_id: Path = attrs.field(converter=Path)
    endpoint: str = attrs.field()
    path_token: str = attrs.field()
    metadata: Metadata = attrs.field()
    access: Access = attrs.field(default=Access())
    path_readme: str | None = attrs.field(default=None)
    paths: list[Path] = attrs.field(factory=list, converter=lambda paths: [Path(p) for p in paths])
    code_repository: str | None = attrs.field(default=None)

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the configuration to a dictionary suitable for Zenodo."""
        data = {
            "access": self.access.to_zenodo(),
            "metadata": self.metadata.to_zenodo(),
            "files": {
                "enabled": len(self.paths) > 0,
                "order": [path.name for path in self.paths],
            },
        }
        if len(self.paths) > 0:
            data["files"]["default_preview"] = self.paths[0].name
        if self.code_repository is not None:
            data["custom_fields"] = {"code:codeRepository": self.code_repository}
        return data


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
        params = {"access_token": self.token, "Accept": "application/vnd.inveniordm.v1+json"}
        return RESTWrapper(self.endpoint, params, verbose=self.verbose)

    # Main API methods

    def create_new_record(self, config: Config) -> dict[str]:
        """Create a new record on Zenodo, which remains in draft until it is published manually."""
        return self.rest.post("records", json=config.to_zenodo())

    def get_record(self, rid: int) -> dict[str]:
        """Get an (un)published record with given id."""
        try:
            # If the dataset is in draft
            res = self.rest.get(f"records/{rid}/draft")
        except RESTError:
            # If the dataset is published
            res = self.rest.get(f"records/{rid}")
        return res

    def update_metadata(self, rid: int, config: Config) -> dict[str]:
        """Update the metadata of a record.

        This is applicable draft records and published records in edit mode.
        """
        return self.rest.put(f"records/{rid}/draft", json=config.to_zenodo())

    def edit_record(self, rid: int):
        """Put a published record into edit mode."""
        self.rest.post(f"records/{rid}/draft")

    def publish_record(self, rid: int):
        """Publish are draft record or a record in edit mode."""
        self.rest.post(f"records/{rid}/draft/actions/publish")

    def start_uploads(self, rid: int, paths: list[Path]):
        self.rest.post(f"records/{rid}/draft/files", json=[{"key": path.name} for path in paths])

    def upload_file(self, rid: int, path: Path):
        """Upload a file. The bucket must belong to a record in draft mode."""
        # Upload the file
        with open(path, "rb") as fh:
            self.rest.put(f"records/{rid}/draft/files/{path.name}/content", data=fh)
        # Commit it
        res = self.rest.post(f"records/{rid}/draft/files/{path.name}/commit")

        if not res["checksum"].startswith("md5:"):
            raise ZenodoError(f"Zenodo returned an unexpected checksum format: {res['checksum']}")

        # Check the checksum and file size
        if not res["size"] == path.size:
            raise ZenodoError(
                f"File size mismatch for {path.name}: "
                f"expected {path.size}, got {res['size']} bytes."
            )
        local_md5 = _compute_md5(path)
        if local_md5 != res["checksum"][4:]:
            raise ZenodoError(
                f"MD5 checksum mismatch for {path.name}, "
                f"local {local_md5}, online {res['checksum'][4:]}."
            )

    def delete_file(self, rid: int, name: str):
        """Delete a file. The file must belong to a record in draft mode."""
        self.rest.delete(f"records/{rid}/draft/files/{name}")

    def get_latest_version(self, parent_rid: int) -> dict[str] | None:
        """Get the latest version of a record."""
        return self.rest.get(f"records/{parent_rid}/versions")

    def create_new_version(self, rid: int) -> dict[str]:
        """Create a new version of a published record. The result is a draft record."""
        return self.rest.post(f"records/{rid}/versions")


def main(argv: list[str] | None = None):
    """Main program."""
    parser = argparse.ArgumentParser(
        prog="sync-zenodo",
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
    try:
        config = cattrs.structure(data, Config)
    except cattrs.ClassValidationError as exc:
        for line in cattrs.transform_error(exc, repr(args.config)):
            print(line)
        raise
    # Override the token path from the config file if the environment variable is set.
    path_token = getenv("REPREP_PATH_ZENODO_TOKEN")
    if path_token is not None:
        config.path_token = path_token
    if args.clean:
        clean_online(config, args.verbose)
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
    parser.add_argument(
        "--clean",
        default=False,
        action="store_true",
        help="Remove all draft data sets before proceeding. "
        "This also deletes the record ID json file.",
    )


def clean_online(config: Config, verbose: bool):
    """Remove all draft data sets on Zenodo."""
    # (Try to) get the token.
    path_token = Path(config.path_token).expand()
    if not path_token.is_file():
        return
    with open(path_token) as fh:
        zenodo = ZenodoWrapper(fh.read().strip(), config.endpoint, verbose=verbose)

    # Get all records.
    response = zenodo.rest.get("user/records")
    for record in response["hits"]["hits"]:
        rid = record["id"]
        if record.get("submitted", False):
            print(f"Record {rid} is already published, skipping.")
            continue
        print(f"Deleting draft record {rid}.")
        try:
            zenodo.rest.delete(f"records/{rid}/draft")
        except RESTError as exc:
            print(f"Failed to delete record {rid}: {exc}")
    if config.path_record_id is not None:
        config.path_record_id.remove_p()


def update_online(config: Config, verbose: bool):
    """Make the online data set up to date with the local information."""
    # Amend inputs when this script is called in a StepUp workflow.
    paths_inp = list(config.paths)
    if config.path_readme is not None:
        paths_inp.append(config.path_readme)
    amend(inp=paths_inp)

    # If present, convert README Markdown file to HTML
    if config.path_readme is not None:
        with open(config.path_readme) as fh:
            description = fh.read()
        if config.path_readme.endswith(".md"):
            md = MarkdownIt()
            description = md.render(description)
        elif not config.path_readme.endswith(".html"):
            raise ZenodoError("The README file must be a Markdown (.md) or HTML (.html) file.")
        config.metadata.description = description

    # Run sanity check on paths: duplicate filenames not allowed.
    paths = {}
    for path in config.paths:
        path = Path(path)
        paths[path.name] = path
    if len(paths) != len(config.paths):
        raise ZenodoError(
            "Zenodo does not support directory layouts. Files must have different names."
        )

    # (Try to) get the token.
    path_token = Path(config.path_token).expand()
    if not path_token.is_file():
        return
    with open(path_token) as fh:
        zenodo = ZenodoWrapper(fh.read().strip(), config.endpoint, verbose=verbose)

    # Check if the parent record ID file exists, and load if it does.
    rid = None
    if config.path_record_id.exists():
        with open(config.path_record_id) as fh:
            try:
                rid = int(fh.read().strip())
            except ValueError as exc:
                raise ZenodoError(f"Invalid record ID in {config.path_record_id}: {exc}") from exc

    # Interact with Zenodo.
    if rid is None:
        # New record, when getting started with a dataset.
        record = _create_new(zenodo, config)
        with open(config.path_record_id, "w") as fh:
            print(record["id"], file=fh)
    else:
        # When a dataset exists, the actions depend on the current status of the record.
        record = zenodo.get_record(rid)
        # At the time of coding, the Zenodo API does not return the full metadata of the record.
        rid = record["id"]
        zenodo_version = record["metadata"]["version"]
        if record.get("submitted", False):
            cmpver = semver.compare(config.metadata.version, zenodo_version)
            if cmpver == 0:
                _check_record_md5(record, paths, config.metadata.version)
                # Unconditionally republish the metadata, because we cannot compare the metadata.
                _republish_metadata(zenodo, rid, config)
            elif cmpver > 0:
                record = _create_new_version(zenodo, rid, config)
                with open(config.path_record_id, "w") as fh:
                    print(record["id"], file=fh)
                _refresh_files(zenodo, record, paths, config.metadata.version)
            else:
                raise ZenodoError(
                    f"The online version ({zenodo_version}) is newer "
                    f"than the local one ({config.metadata.version})."
                )
        else:
            _refresh_files(zenodo, record, paths, config.metadata.version)
            # Unconditionally update the metadata, because we cannot compare the metadata.
            zenodo.update_metadata(rid, config)


def _create_new(zenodo: ZenodoWrapper, config: Config) -> dict[str, Any]:
    """Create a new record on Zenodo."""
    record = zenodo.create_new_record(config)

    # Declare the files to be uploaded.
    zenodo.start_uploads(record["id"], config.paths)

    # Actual uploads, one by one.
    for path in config.paths:
        print(f"Uploading {path}")
        zenodo.upload_file(record["id"], path)
    return record


def _compute_md5(path: str) -> bool:
    """Compute the MD5 sum of a file and compare to the given checksum."""
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, hashlib.md5).hexdigest()


def _check_record_md5(record: dict[str], paths: dict[str, Path], version: str):
    """Sanity check of MD5 hashes received from Zenodo"""
    for file in record["files"]:
        if file["key"] not in paths:
            raise ZenodoError(
                f"File {file['key']} exists online but not locally ({version}, published)"
            )
        path = paths[file["key"]]
        local_md5 = _compute_md5(path)
        if local_md5 != file["checksum"][4:]:
            raise ValueError(
                f"MD5 Checksum mismatch for {path} ({version}, published), "
                f"local: {local_md5}, online: {file['checksum'][4:]}"
            )
    online_names = {file["key"] for file in record["files"]}
    for name in paths:
        if name not in online_names:
            raise OSError(f"File {name} exists locally but not online ({version}, published)")


def _republish_metadata(zenodo: ZenodoWrapper, rid: int, config: Config):
    """Put a record in edit mode, update the metadata and publish again."""
    print(f"Editing metadata and publishing same version ({config.metadata.version}) again.")
    zenodo.edit_record(rid)
    zenodo.update_metadata(rid, config)
    zenodo.publish_record(rid)


def _create_new_version(zenodo: ZenodoWrapper, rid: int, config: Config) -> dict[str]:
    """Create a new version of the dataset and refresh the metadata."""
    print(f"Creating a new version ({config.metadata.version})")
    record = zenodo.create_new_version(rid)
    return zenodo.update_metadata(record["id"], config)


def _refresh_files(
    zenodo: ZenodoWrapper, record: dict[str], paths: dict[str, Path], version: str
) -> bool:
    """Refresh the online files.

    This function only uploads files that do not exist online yet or have changed locally.
    Files removed from the local YAML config will also be removed online.
    """
    changed = False
    for file in record["files"]:
        if not file["checksum"].startswith("md5:"):
            raise ZenodoError(f"Zenodo returned an unexpected checksum format: {file['checksum']}")
        if file["key"] not in paths:
            print(f"Deleting {file['key']} ({version}, draft)")
            zenodo.delete_file(record["id"], file["key"])
            changed = True
        else:
            path = paths[file["key"]]
            local_md5 = _compute_md5(path)
            if local_md5 != file["checksum"][4:]:
                print(f"Replacing {path} ({version}, draft)")
                zenodo.delete_file(record["id"], file["key"])
                zenodo.start_uploads(record["id"], [path])
                zenodo.upload_file(record["id"], path)
                changed = True
    online_names = {file["key"] for file in record["files"]}
    for name, path in paths.items():
        if name not in online_names:
            print(f"Uploading {path} ({version}, draft)")
            zenodo.start_uploads(record["id"], [path])
            zenodo.upload_file(record["id"], path)
            changed = True
    return changed


if __name__ == "__main__":
    main(sys.argv[1:])
