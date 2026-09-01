# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Synchronization of local datasets with drafts on Zenodo.

This script synchronizes your local version of a dataset
with the (draft of) this dataset on Zenodo.
This simplifies your interaction with Zenodo to the following steps:

1. Prepare a personal token
2. Write metadata in a configuration file, in YAML, JSON or TOML format.
3. Include this script in your workflow to automatically sync data.
4. Publish the dataset through the Zenodo web interface.

After publication, only metadata can be updated, not the actual files.
If you need to upload different files, change the version in the config file.
This will result in a new draft that you can publish when it is final.

This script offers a simplified interface to Zenodo.
It does not try to mirror all of Zenodo's API features.

This module talks to the InvenioRDM API of Zenodo, `/api/records`,
not to the legacy deposit API that https://developers.zenodo.org/ documents,
and not to the legacy `.zenodo.json` file that Zenodo reads for a GitHub release.
The three use different names for overlapping metadata,
which the documentation of `srr-sync-zenodo` explains in more detail.
Zenodo does not document the InvenioRDM API itself,
but InvenioRDM, the software that Zenodo runs, does:

- https://inveniordm.docs.cern.ch/reference/rest_api_index/
- https://inveniordm.docs.cern.ch/reference/metadata/

As observed in June 2025, the Zenodo deployment of this API was not fully stable,
and some of the features implemented in this module were deduced from the Zenodo web interface.
"""

import argparse
import datetime
import functools
import hashlib
import ipaddress
import json
import os
import re
import sys
import tomllib
from collections.abc import Callable, Mapping, Sequence
from importlib import resources
from typing import Any, get_args, get_origin
from urllib.parse import quote, urlparse

import attrs
import cattrs
import idutils
import requests
import yaml
from cattrs.cols import list_structure_factory
from cattrs.gen import make_dict_structure_fn
from markdown_it import MarkdownIt
from path import Path
from rich.console import Console
from rich.json import JSON

from stepup.reprep.utils import MAX_NUM_ZENODO_FILES, check_zenodo_paths

__all__ = ("main",)


CONSOLE = Console(soft_wrap=True, highlight=False)

REQUEST_TIMEOUT = 60.0
"""The number of seconds to wait for Zenodo, before a request is considered lost.

This bounds the wait for the connection and the wait for the next byte of the response,
not the time it takes to send the body of an upload,
so a large file may well take longer than this to transfer.
"""


# Comparison is left to `Exception`, which compares by identity,
# because two errors that happen to carry the same message are not the same error.
@attrs.define(eq=False)
class RESTError(Exception):
    """Raised when a REST API call is not successful."""

    message: str = attrs.field()
    """The complete diagnosis, naming the request and quoting the response of Zenodo."""

    status_code: int | None = attrs.field(default=None)
    """The status code of the response, or `None` when the request never received one."""

    def __str__(self) -> str:
        return self.message


class ZenodoError(Exception):
    """Raised when something must be corrected before the dataset can be synchronized.

    The message is the complete diagnosis,
    so `srr-sync-zenodo` reports it without a traceback and exits with a nonzero status.
    """


@attrs.define
class RESTWrapper:
    """Wrapper for REST APIs that use JSON input (mostly) and output (always)."""

    endpoint: str = attrs.field()
    headers: dict[str, str] = attrs.field()
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
            Headers given here are merged into the ones stored in this wrapper.
            The timeout defaults to `REQUEST_TIMEOUT` and can be overridden here.

        Returns
        -------
        response_data
            Deserialized JSON response data.

        Raises
        ------
        RESTError
            When Zenodo does not accept the request or cannot be reached.
        """
        url = f"{self.endpoint}/{loc}"
        if self.verbose:
            CONSOLE.print(f"[b]{method} {url}[/b]")
            if "json" in kwargs:
                CONSOLE.print("[b]REQUEST[/b]")
                CONSOLE.print(JSON.from_data(kwargs["json"]))
        headers = self.headers | kwargs.pop("headers", {})
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        try:
            res = requests.request(method, url, headers=headers, **kwargs)
        except requests.RequestException as exc:
            # A request that never reaches Zenodo, or whose response never arrives,
            # is reported like a refused one, so the caller has a single error to handle.
            raise RESTError(f"Failed {method} {url}: {exc}") from exc
        if not res.ok:
            # The body is passed on as it arrived, because an error is not always JSON.
            # A gateway between here and Zenodo may answer with an HTML page instead.
            raise RESTError(
                f"Failed {method} {url}: {res.status_code}\n{res.text}", res.status_code
            )
        data = None if len(res.text) == 0 else res.json()
        if self.verbose:
            CONSOLE.print("[b]RESPONSE[/b]")
            CONSOLE.print(JSON.from_data(data))
            CONSOLE.print()
        return data

    def get(self, loc: str, **kwargs):
        """Send a GET HTTP request. See `request` method for details."""
        return self.request("GET", loc, **kwargs)

    def post(self, loc: str, **kwargs):
        """Send a POST HTTP request. See `request` method for details."""
        return self.request("POST", loc, **kwargs)

    def put(self, loc: str, **kwargs):
        """Send a PUT HTTP request. See `request` method for details."""
        return self.request("PUT", loc, **kwargs)

    def delete(self, loc: str, **kwargs):
        """Send a DELETE HTTP request. See `request` method for details."""
        return self.request("DELETE", loc, **kwargs)


VOCABULARIES_FILENAME = "zenodo_vocabularies.yaml"
"""Data file holding the controlled vocabularies of Zenodo.

It is generated by `tools/update_zenodo_vocabularies.py` in the source repository.
"""


@functools.cache
def _load_vocabularies() -> dict[str, frozenset[str]]:
    """Load the controlled vocabularies of Zenodo.

    Returns
    -------
    vocabularies
        The identifiers Zenodo accepts, for each vocabulary name in its API.
        The keys of the data file that start with an underscore are left out,
        because they hold bookkeeping of the refresh instead of a vocabulary.
    """
    text = resources.files(__package__).joinpath(VOCABULARIES_FILENAME).read_text(encoding="utf-8")
    return {
        name: frozenset(ids)
        for name, ids in yaml.safe_load(text).items()
        if not name.startswith("_")
    }


def _in_vocabulary(name: str) -> Callable[[Any, attrs.Attribute, str], None]:
    """Create a validator for an identifier taken from a controlled vocabulary of Zenodo.

    Parameters
    ----------
    name
        The name of the vocabulary in Zenodo's API, e.g. `code:developmentStatus`.

    Returns
    -------
    validator
        An attrs validator rejecting identifiers outside of the vocabulary.
    """

    def validate(instance, attribute, value):
        if value not in _load_vocabularies()[name]:
            raise ValueError(
                f"Invalid identifier for '{attribute.name}': {value!r}. "
                f"Zenodo takes it from the {name} vocabulary and matches it case-sensitively. "
                f"See https://zenodo.org/api/vocabularies/{name} for the valid identifiers."
            )

    return validate


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


def _check_scheme(name: str, scheme: str):
    """Check the name of an identifier scheme.

    Parameters
    ----------
    name
        The name of the attribute holding the scheme, used in the error message.
    scheme
        The scheme to check.

    Raises
    ------
    ValueError
        When Zenodo does not know the scheme.
    """
    if scheme not in IDENTIFIER_SCHEMES:
        raise ValueError(
            f"Unknown identifier scheme for '{name}': {scheme!r}. "
            f"Zenodo reads one of: {', '.join(sorted(IDENTIFIER_SCHEMES))}."
        )


def _check_identifier(scheme: str, identifier: str):
    """Check an identifier against the format of its scheme.

    Parameters
    ----------
    scheme
        The scheme of the identifier, which Zenodo must know.
    identifier
        The identifier to check.

    Raises
    ------
    ValueError
        When the identifier does not have the format of the scheme.
    """
    if not IDENTIFIER_SCHEMES[scheme](identifier):
        raise ValueError(
            f"Invalid identifier for scheme {scheme}: {identifier!r}. "
            "Please check the identifier format."
        )


def _to_zenodo_object(**values: Any) -> dict[str, Any]:
    """Build a JSON object for Zenodo, leaving out the keys whose value is not set.

    Parameters
    ----------
    values
        The candidate keys of the object, with the value of the corresponding attribute.

    Returns
    -------
    object
        The keys whose value is set, in the order in which they were given.
    """
    return {key: value for key, value in values.items() if value is not None and value != []}


@attrs.define
class Organization:
    """A subset of InvenioRDM affiliation / funder."""

    name: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.min_len(1)),
    )
    """Name of the organization, e.g. a university, research institute or funding agency."""

    ror: str | None = attrs.field(default=None)
    """The Research Organization Registry identifier."""

    @ror.validator
    def _validate_ror(self, attribute, value):
        """Validate the ROR identifiers."""
        if not (value is None or idutils.is_ror(value)):
            raise ValueError(
                f"Invalid ROR identifier for '{attribute.name}': {value!r}. "
                "Zenodo reads nine characters starting with a zero, e.g. '03yrm5c26'."
            )

    def __attrs_post_init__(self):
        if not ((self.name is None) ^ (self.ror is None)):
            raise ValueError("Exactly one of 'name' or 'ror' must be set for an organization.")

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the organization to a dictionary suitable for Zenodo."""
        return {"name": self.name} if self.ror is None else {"id": self.ror}


@attrs.define
class Creator:
    """A subset of InvenioRDM creator."""

    family_name: str = attrs.field(validator=attrs.validators.min_len(1))
    """Family name.

    Zenodo requires this, because creators are deposited as persons, not as organizations.
    """

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
        return _to_zenodo_object(
            person_or_org=_to_zenodo_object(
                type="personal",
                family_name=self.family_name,
                given_name=self.given_name,
                identifiers=[
                    {"scheme": key, "identifier": value} for key, value in self.identifiers.items()
                ],
            ),
            affiliations=[aff.to_zenodo() for aff in self.affiliations],
        )


@attrs.define
class Access:
    """A subset of InvenioRDM Access.

    https://inveniordm.docs.cern.ch/reference/metadata/#access
    """

    record: str = attrs.field(
        default="public",
        validator=attrs.validators.in_(["public", "restricted"]),
    )
    """The access level of the record.

    Public means that the record is visible to everyone.
    """

    files: str = attrs.field(
        default="public",
        validator=attrs.validators.in_(["public", "restricted"]),
    )
    """The access level of the files.

    Public means that the files are visible to everyone.
    """

    def to_zenodo(self) -> dict[str, str]:
        """Convert the access configuration to a dictionary suitable for Zenodo."""
        return {
            "record": self.record,
            "files": self.files,
        }


@attrs.define
class Identifier:
    """An identifier of something Zenodo does not store as a record, e.g. an award."""

    identifier: str = attrs.field()
    """The identifier itself, e.g. '10.5281/zenodo.1234567'."""

    scheme: str | None = attrs.field(default=None)
    """The scheme of the identifier, e.g. 'doi' or 'url'.

    Zenodo derives the scheme from the identifier when it is not given.
    """

    @scheme.validator
    def _validate_scheme(self, attribute, value):
        """Validate the scheme and the identifier it describes."""
        if value is None:
            return
        _check_scheme(attribute.name, value)
        _check_identifier(value, self.identifier)

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the identifier to a dictionary suitable for Zenodo."""
        return _to_zenodo_object(scheme=self.scheme, identifier=self.identifier)


@attrs.define
class Related:
    """A subset of InvenioRDM related identifier."""

    scheme: str = attrs.field()
    """The scheme of the identifier, e.g. 'doi' or 'arxiv'."""

    @scheme.validator
    def _validate_scheme(self, attribute, value):
        """Validate the scheme."""
        _check_scheme(attribute.name, value)

    identifier: str = attrs.field()
    """The identifier itself, e.g. '10.5281/zenodo.1234567'."""

    @identifier.validator
    def _validate_identifier(self, attribute, value):
        """Validate the identifier."""
        _check_identifier(self.scheme, value)

    relation_type: str = attrs.field(validator=_in_vocabulary("relationtypes"))
    """How the record relates to the identified resource, e.g. 'issupplementto'."""

    resource_type: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(_in_vocabulary("resourcetypes")),
    )
    """The kind of resource the identifier points to, e.g. 'publication-article'."""

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
    """A subset of InvenioRDM award information."""

    id: str | None = attrs.field(default=None)
    """The award ID, e.g. '123456'."""

    title: str | None = attrs.field(default=None)
    """The title of the award, e.g. 'Research Excellence Award'."""

    number: str | None = attrs.field(default=None)
    """The award number, e.g. 'RE-123456'."""

    identifiers: list[Identifier] = attrs.field(factory=list)
    """Identifiers of the award, e.g. its DOI or the URL of its description."""

    def __attrs_post_init__(self):
        if not ((self.id is None) ^ (self.title is None and self.number is None)):
            raise ValueError(
                "An award is described either by 'id', "
                "or by 'title' and 'number', of which at least one must be given. "
                "Zenodo fills in the title and the number of an award it already knows, "
                "so free text next to an 'id' would be ignored."
            )

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the award information to a dictionary suitable for Zenodo."""
        return _to_zenodo_object(
            id=self.id,
            title=None if self.title is None else {"en": self.title},
            number=self.number,
            identifiers=[identifier.to_zenodo() for identifier in self.identifiers],
        )


@attrs.define
class Funding:
    """A subset of InvenioRDM funding information."""

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
    """Lower case the license identifiers, which Zenodo takes from SPDX in lower case."""
    return [lic.lower() for lic in arg]


MIN_DESCRIPTION_LEN = 3
"""The shortest description Zenodo accepts."""


@attrs.define
class Metadata:
    """A subset of InvenioRDM metadata.

    https://inveniordm.docs.cern.ch/reference/metadata/#metadata

    Zenodo requires `title`, `resource_type` and `creators`,
    and enforces the length bounds checked below.
    These requirements were read on 2026-08-30 from `MetadataSchema` in
    `invenio_rdm_records/services/schemas/metadata.py`.
    A deposit that violates them fails, so they are checked before contacting Zenodo.
    """

    title: str = attrs.field(validator=attrs.validators.min_len(3))

    version: str = attrs.field(
        validator=[attrs.validators.min_len(1), attrs.validators.max_len(191)]
    )
    """The version of the dataset, in any convention you like.

    Zenodo stores this as free text and does not order the versions of a dataset by it,
    so `srr-sync-zenodo` only tests it for equality with the versions published on Zenodo,
    to decide whether a new version has to be created.
    It must be non-empty, because it is the only thing identifying the local version.
    """

    resource_type: str = attrs.field(validator=_in_vocabulary("resourcetypes"))

    publisher: str = attrs.field(validator=attrs.validators.min_len(1))
    """The name under which the dataset is made available, e.g. `Zenodo`.

    Zenodo accepts a draft without a publisher but refuses to publish it,
    because it needs one to register a DOI,
    so a publisher is required here to fail before the record is created.
    """

    creators: list[Creator] = attrs.field(validator=attrs.validators.min_len(1))

    keywords: list[str] = attrs.field(factory=list)
    """A list of keywords to describe the dataset.

    Zenodo has no keyword field and stores these as free text subjects.
    """

    license: list[str] = attrs.field(
        factory=list,
        converter=_convert_license,
        validator=attrs.validators.deep_iterable(_in_vocabulary("licenses")),
    )

    copyright: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.min_len(1)),
    )

    languages: list[str] = attrs.field(
        factory=list, validator=attrs.validators.deep_iterable(_in_vocabulary("languages"))
    )
    """A list of ISO 639-3 language codes, e.g. `eng` for English or `fra` for French."""

    description: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.min_len(MIN_DESCRIPTION_LEN)),
    )

    related: list[Related] = attrs.field(factory=list)

    funding: list[Funding] = attrs.field(factory=list)

    def to_zenodo(self, publication_date: str | None = None) -> dict[str, Any]:
        """Convert the metadata to a dictionary suitable for Zenodo.

        Parameters
        ----------
        publication_date
            The publication date to send to Zenodo, in ISO format.
            When `None`, today's date is used,
            which is the only sensible guess for a record that is not published yet.
        """
        if publication_date is None:
            publication_date = datetime.date.today().isoformat()
        return _to_zenodo_object(
            title=self.title,
            version=self.version,
            resource_type={"id": self.resource_type},
            publisher=self.publisher,
            subjects=[{"subject": keyword} for keyword in self.keywords],
            rights=[{"id": lic} for lic in self.license],
            copyright=self.copyright,
            languages=[{"id": lang} for lang in self.languages],
            description=self.description,
            creators=[creator.to_zenodo() for creator in self.creators],
            publication_date=publication_date,
            related_identifiers=[rel.to_zenodo() for rel in self.related],
            funding=[fund.to_zenodo() for fund in self.funding],
        )


URL_SCHEMES = frozenset(["http", "https", "ftp", "ftps"])
"""The URL schemes that Zenodo accepts."""


def _is_acceptable_host(host: str) -> bool:
    """Tell whether Zenodo accepts a host name."""
    if host == "localhost":
        return True
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return True
    labels = host.split(".")
    return len(labels) > 1 and all(labels) and len(labels[-1]) >= 2


# Zenodo validates these URLs with `marshmallow.validate.URL`,
# reached through `_valid_url` in `invenio_rdm_records/services/schemas/metadata.py`.
# As observed on 2026-08-30, that accepts `http`, `https`, `ftp` and `ftps`,
# and requires a host that carries a top level domain of at least two characters,
# or is `localhost`, or is an IP literal.
# The check below deliberately differs on one point:
# an internationalized host name such as `https://académie.fr` passes here,
# while Zenodo rejects it, because an IDNA round trip is more machinery than this check deserves.
def _validate_url(instance, attribute, value):
    """Validate a URL that Zenodo stores as a plain string."""
    try:
        parsed = urlparse(value)
        ok = parsed.scheme in URL_SCHEMES and parsed.hostname is not None
        ok = ok and _is_acceptable_host(parsed.hostname)
    except ValueError:
        # `urlparse` rejects a malformed IPv6 literal such as `https://[::1/x`.
        ok = False
    if not ok:
        raise ValueError(
            f"Invalid URL for '{attribute.name}': {value!r}. "
            "Zenodo reads an http, https, ftp or ftps URL "
            "whose host name carries a top level domain of at least two characters."
        )


def _to_vocabulary_id(value: str) -> dict[str, str]:
    """Convert an identifier into the object Zenodo expects for a single vocabulary term."""
    return {"id": value}


def _to_vocabulary_ids(values: list[str]) -> list[dict[str, str]]:
    """Convert identifiers into the objects Zenodo expects for repeated vocabulary terms."""
    return [{"id": value} for value in values]


def _to_nested(value: Any) -> dict[str, Any]:
    """Convert a nested value object into the JSON object Zenodo expects."""
    return value.to_zenodo()


@attrs.define
class Journal:
    """The journal in which the resource appeared."""

    title: str | None = attrs.field(default=None)
    """The name of the journal."""

    issue: str | None = attrs.field(default=None)
    """The issue in which the resource appeared, e.g. '3'."""

    volume: str | None = attrs.field(default=None)
    """The volume in which the resource appeared, e.g. '42'."""

    pages: str | None = attrs.field(default=None)
    """The pages of the resource within the issue, e.g. '123-145'."""

    issn: str | None = attrs.field(default=None)
    """The International Standard Serial Number of the journal, e.g. '0378-5955'."""

    @issn.validator
    def _validate_issn(self, attribute, value):
        """Validate the ISSN, which Zenodo checks with `idutils.is_issn`."""
        if not (value is None or idutils.is_issn(value)):
            raise ValueError(
                f"Invalid ISSN for '{attribute.name}': {value!r}. "
                "Zenodo reads eight digits ending in a check digit, e.g. '0378-5955'."
            )

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the journal reference to a dictionary suitable for Zenodo."""
        return _to_zenodo_object(
            title=self.title,
            issue=self.issue,
            volume=self.volume,
            pages=self.pages,
            issn=self.issn,
        )


@attrs.define
class Meeting:
    """The meeting at which the resource was presented."""

    title: str | None = attrs.field(default=None)
    """The full title of the meeting."""

    acronym: str | None = attrs.field(default=None)
    """The short name of the meeting, e.g. 'ESOF24'."""

    dates: str | None = attrs.field(default=None)
    """The dates of the meeting as free text, which Zenodo stores without parsing it."""

    place: str | None = attrs.field(default=None)
    """The location of the meeting, e.g. 'Ghent, Belgium'."""

    session: str | None = attrs.field(default=None)
    """The session of the meeting, e.g. 'VI'."""

    session_part: str | None = attrs.field(default=None)
    """The part within the session, e.g. '1'."""

    url: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(_validate_url),
    )
    """The website of the meeting."""

    identifiers: list[Identifier] = attrs.field(factory=list)
    """Identifiers of the meeting, e.g. the DOI of its proceedings."""

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the meeting to a dictionary suitable for Zenodo."""
        return _to_zenodo_object(
            title=self.title,
            acronym=self.acronym,
            dates=self.dates,
            place=self.place,
            session=self.session,
            session_part=self.session_part,
            url=self.url,
            identifiers=[identifier.to_zenodo() for identifier in self.identifiers],
        )


@attrs.define
class Imprint:
    """The book or report in which the resource appeared."""

    title: str | None = attrs.field(default=None)
    """The title of the book in which the resource appeared as a chapter."""

    isbn: str | None = attrs.field(default=None)
    """The International Standard Book Number, e.g. '978-3-16-148410-0'."""

    @isbn.validator
    def _validate_isbn(self, attribute, value):
        """Validate the ISBN, which Zenodo checks with `idutils.is_isbn`."""
        if not (value is None or idutils.is_isbn(value)):
            raise ValueError(
                f"Invalid ISBN for '{attribute.name}': {value!r}. "
                "Zenodo reads a ten or thirteen digit number ending in a check digit, "
                "e.g. '978-3-16-148410-0'."
            )

    pages: str | None = attrs.field(default=None)
    """The pages of the resource within the book, e.g. '15-30'."""

    place: str | None = attrs.field(default=None)
    """The place of publication, e.g. 'Ghent, Belgium'."""

    edition: str | None = attrs.field(default=None)
    """The edition of the book, e.g. '2nd'."""

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the imprint to a dictionary suitable for Zenodo."""
        return _to_zenodo_object(
            title=self.title,
            isbn=self.isbn,
            pages=self.pages,
            place=self.place,
            edition=self.edition,
        )


PLAIN_DATE_PATTERN = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
"""A date written as a year, a year and a month, or a full calendar date."""


# Zenodo validates the thesis dates as EDTF level 2,
# which also covers uncertain and approximate expressions such as `1984~` or `1984-06-uu`.
# That grammar is more than this module wants to reimplement,
# so only a value that looks like a plain calendar date is checked here.
# Anything else is passed on to Zenodo, which has the final say.
def _validate_edtf_date(instance, attribute, value):
    """Validate a date that Zenodo reads as an EDTF level 2 expression."""
    if value is None or PLAIN_DATE_PATTERN.match(value) is None:
        return
    parts = [int(part) for part in value.split("-")]
    parts.extend([1] * (3 - len(parts)))
    try:
        datetime.date(*parts)
    except ValueError as exc:
        raise ValueError(
            f"Impossible date for '{attribute.name}': {value!r}. {exc}. "
            "Zenodo reads a date as an EDTF level 2 expression, "
            "e.g. '2024-06-15', '2024-06', '2024' or '1984~'."
        ) from exc


@attrs.define
class Thesis:
    """The dissertation of which the resource is the outcome."""

    university: str | None = attrs.field(default=None)
    """The institution that awarded the degree."""

    department: str | None = attrs.field(default=None)
    """The department within the institution."""

    type: str | None = attrs.field(default=None)
    """The kind of thesis, e.g. 'PhD' or 'Master'."""

    date_submitted: str | None = attrs.field(default=None, validator=_validate_edtf_date)
    """The date on which the thesis was submitted, e.g. '2024-06-15'."""

    date_defended: str | None = attrs.field(default=None, validator=_validate_edtf_date)
    """The date on which the thesis was defended, e.g. '2024-09-23'."""

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the thesis to a dictionary suitable for Zenodo."""
        return _to_zenodo_object(
            university=self.university,
            department=self.department,
            type=self.type,
            date_submitted=self.date_submitted,
            date_defended=self.date_defended,
        )


CUSTOM_FIELD = "custom_field"
"""Metadata key under which an attribute of `CustomFields` stores its `CustomFieldSpec`."""


@attrs.define(frozen=True)
class CustomFieldSpec:
    """How an attribute of `CustomFields` maps onto a custom field of Zenodo."""

    name: str = attrs.field()
    """The name of the custom field in Zenodo's API, e.g. `code:codeRepository`."""

    to_zenodo: Callable[[Any], Any] = attrs.field(default=lambda value: value)
    """Convert the value of the attribute into the JSON value that Zenodo expects."""


@attrs.define
class CustomFields:
    """A subset of the custom fields with which Zenodo extends the InvenioRDM record.

    Attributes are named as in the config file,
    which is more intuitive than the namespaced names Zenodo uses.
    Each attribute carries a `CustomFieldSpec` in its metadata,
    holding the Zenodo name and the conversion to the JSON value Zenodo expects.
    An attribute left at its default is not sent to Zenodo,
    and neither is a nested object all of whose keys are unset,
    because Zenodo expects at least one key in such an object.

    The shapes below were read on 2026-08-30 from the software Zenodo runs:
    the `code:` and `dc:` fields from `site/zenodo_rdm/custom_fields` in `zenodo/zenodo-rdm`,
    and the four object fields from `invenio_rdm_records/contrib` in `invenio-rdm-records`.
    A field whose name starts with `legacy:` is deliberately absent:
    only the loader that reads a `.zenodo.json` of a GitHub release understands those,
    so the InvenioRDM API used here would drop them without saying so.
    """

    code_repository: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(_validate_url),
        metadata={CUSTOM_FIELD: CustomFieldSpec("code:codeRepository")},
    )
    """URL of the repository in which the code is hosted."""

    development_status: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(_in_vocabulary("code:developmentStatus")),
        metadata={CUSTOM_FIELD: CustomFieldSpec("code:developmentStatus", _to_vocabulary_id)},
    )
    """The development status of the software."""

    programming_languages: list[str] = attrs.field(
        factory=list,
        validator=attrs.validators.deep_iterable(_in_vocabulary("code:programmingLanguages")),
        metadata={CUSTOM_FIELD: CustomFieldSpec("code:programmingLanguage", _to_vocabulary_ids)},
    )
    """The programming languages in which the software is written."""

    rights_holder: list[str] = attrs.field(
        factory=list,
        metadata={CUSTOM_FIELD: CustomFieldSpec("dc:rightsHolder")},
    )
    """The parties that hold the rights to the resource.

    Use this for a rights holder that is not one of the creators,
    e.g. the institution that employs them.
    """

    journal: Journal | None = attrs.field(
        default=None,
        metadata={CUSTOM_FIELD: CustomFieldSpec("journal:journal", _to_nested)},
    )
    """The journal in which the resource appeared."""

    meeting: Meeting | None = attrs.field(
        default=None,
        metadata={CUSTOM_FIELD: CustomFieldSpec("meeting:meeting", _to_nested)},
    )
    """The meeting at which the resource was presented."""

    imprint: Imprint | None = attrs.field(
        default=None,
        metadata={CUSTOM_FIELD: CustomFieldSpec("imprint:imprint", _to_nested)},
    )
    """The book or report in which the resource appeared."""

    thesis: Thesis | None = attrs.field(
        default=None,
        metadata={CUSTOM_FIELD: CustomFieldSpec("thesis:thesis", _to_nested)},
    )
    """The dissertation of which the resource is the outcome."""

    def to_zenodo(self) -> dict[str, Any]:
        """Convert the custom fields to a dictionary suitable for Zenodo."""
        result = {}
        for attribute in attrs.fields(type(self)):
            value = getattr(self, attribute.name)
            if value is None:
                continue
            spec = attribute.metadata[CUSTOM_FIELD]
            converted = spec.to_zenodo(value)
            if not converted:
                continue
            result[spec.name] = converted
        return result


def _convert_endpoint(arg: str) -> str:
    """Remove the trailing slashes of an endpoint URL."""
    return arg.rstrip("/")


DEFAULT_ENDPOINT = "https://sandbox.zenodo.org/api"
"""The Zenodo instance to talk to when the config file names none.

This is the sandbox, so that a first run cannot deposit anything on the production instance.
"""


@attrs.define
class Config:
    """Configuration of the sync-zenodo script.

    An object of this class is created from data loaded from a local config file.
    """

    path_record_id: Path = attrs.field(converter=Path)
    metadata: Metadata = attrs.field()
    endpoint: str = attrs.field(
        default=DEFAULT_ENDPOINT, converter=_convert_endpoint, validator=_validate_url
    )
    custom_fields: CustomFields = attrs.field(factory=CustomFields)
    access: Access = attrs.field(factory=Access)

    def to_zenodo(self, paths: list[Path], publication_date: str | None = None) -> dict[str, Any]:
        """Convert the configuration to a dictionary suitable for Zenodo.

        Parameters
        ----------
        paths
            The files to be uploaded to Zenodo.
        publication_date
            The publication date to send to Zenodo, in ISO format.
            When `None`, today's date is used.
        """
        data = {
            "access": self.access.to_zenodo(),
            "metadata": self.metadata.to_zenodo(publication_date),
            "custom_fields": self.custom_fields.to_zenodo(),
            "files": {
                "enabled": len(paths) > 0,
                "order": [path.name for path in paths],
            },
        }
        if len(paths) > 0:
            data["files"]["default_preview"] = paths[0].name
        return data


INVENIORDM_MIMETYPE = "application/vnd.inveniordm.v1+json"
"""The representation of a record that this module asks Zenodo for.

Without this Accept header, Zenodo answers with its legacy record schema,
which names and shapes several fields differently.
As observed on 2026-08-30, the two differ in the fields this module reads:
`files` is an object with an `entries` mapping here and a list in the legacy schema,
and a published record is marked with `is_published` here and with `submitted` there.
"""


MD5_PREFIX = "md5:"
"""The algorithm with which Zenodo prefixes the checksum of a file."""


SEARCH_PAGE_SIZE = 100
"""The number of records requested per page when a paginated search result is collected.

As observed on 2026-08-30, Zenodo refuses a page larger than this.
"""


MAX_SEARCH_PAGES = 100
"""The number of pages to request before a paginated search result is considered endless.

This bounds the work of collecting a search result,
also when Zenodo keeps sending full pages.
"""


def _file_loc(rid: str, name: str) -> str:
    """Build the address of one file of a draft record.

    Parameters
    ----------
    rid
        The id of the record.
    name
        The name of the file.
        It becomes a single path segment, so every character that delimits a URL is escaped.

    Returns
    -------
    loc
        The address of the file, to be appended after the endpoint.
    """
    return f"records/{rid}/draft/files/{quote(name, safe='')}"


@attrs.define
class ZenodoWrapper:
    """Python interface to a subset of the Zenodo API."""

    token: str = attrs.field()
    endpoint: str = attrs.field(default=DEFAULT_ENDPOINT)
    verbose: bool = attrs.field(default=False)
    rest: RESTWrapper = attrs.field(init=False)

    @rest.default
    def _default_rest(self):
        """Set the default REST wrapper."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": INVENIORDM_MIMETYPE,
        }
        return RESTWrapper(self.endpoint, headers, verbose=self.verbose)

    # Main API methods

    def create_new_record(self, config: Config, paths: list[Path]) -> dict[str, Any]:
        """Create a new record on Zenodo, which remains in draft until it is published manually.

        The files are declared here, even though none of them is uploaded yet,
        because Zenodo refuses an upload to a record whose files it does not have enabled.
        """
        return self.rest.post("records", json=config.to_zenodo(paths))

    def get_record(self, rid: str) -> dict[str, Any]:
        """Get an (un)published record with given id.

        The draft is preferred, because it carries the changes that are not published yet.
        Only a record without a draft is read as a published one,
        so that a refused or lost request is not mistaken for a published dataset.
        """
        try:
            res = self.rest.get(f"records/{rid}/draft")
        except RESTError as exc:
            if exc.status_code != 404:
                raise
            res = self.rest.get(f"records/{rid}")
        return res

    def update_metadata(
        self, rid: str, config: Config, paths: list[Path], publication_date: str | None = None
    ) -> dict[str, Any]:
        """Update the metadata of a record.

        This is applicable to draft records and published records in edit mode.
        The publication date of a record that is already published
        must be passed in, because it is not part of the local configuration
        and a metadata update would otherwise move it to today.
        """
        return self.rest.put(f"records/{rid}/draft", json=config.to_zenodo(paths, publication_date))

    def edit_record(self, rid: str):
        """Put a published record into edit mode."""
        self.rest.post(f"records/{rid}/draft")

    def publish_record(self, rid: str):
        """Publish a draft record or a record in edit mode."""
        self.rest.post(f"records/{rid}/draft/actions/publish")

    def start_uploads(self, rid: str, paths: list[Path]):
        """Declare the files that will be uploaded to a record in draft mode.

        Nothing is sent when there are no files,
        because Zenodo rejects a request that declares none.
        """
        if len(paths) == 0:
            return
        self.rest.post(f"records/{rid}/draft/files", json=[{"key": path.name} for path in paths])

    def upload_file(self, rid: str, path: Path):
        """Upload a file to a record that is in draft mode."""
        loc = _file_loc(rid, path.name)
        with open(path, "rb") as fh:
            self.rest.put(f"{loc}/content", data=fh)
        res = self.rest.post(f"{loc}/commit")
        if res.get("size") != path.size:
            raise ZenodoError(
                f"File size mismatch for {path.name}: "
                f"expected {path.size}, got {res.get('size')} bytes."
            )
        local_md5 = _compute_md5(path)
        online_md5 = _entry_md5(res)
        if local_md5 != online_md5:
            raise ZenodoError(
                f"MD5 checksum mismatch for {path.name}, local {local_md5}, online {online_md5}."
            )

    def delete_file(self, rid: str, name: str):
        """Delete a file.

        The file must belong to a record in draft mode.
        """
        self.rest.delete(_file_loc(rid, name))

    def get_all_pages(self, loc: str) -> list[dict[str, Any]]:
        """Collect the records of a paginated search result.

        Parameters
        ----------
        loc
            The address of the search result, appended after the endpoint.

        Returns
        -------
        records
            The records of every page, in the order Zenodo returns them.

        Raises
        ------
        ZenodoError
            When Zenodo sends more than `MAX_SEARCH_PAGES` full pages.
        """
        records = []
        for page in range(1, MAX_SEARCH_PAGES + 1):
            data = self.rest.get(loc, params={"page": page, "size": SEARCH_PAGE_SIZE})
            hits = _search_hits(data)
            records.extend(hits)
            if len(hits) < SEARCH_PAGE_SIZE:
                break
        else:
            raise ZenodoError(
                f"Zenodo sent {MAX_SEARCH_PAGES} full pages of results for {loc}, "
                "which is more than this module collects."
            )
        return records

    def get_versions(self, rid: str) -> list[dict[str, Any]]:
        """Get all published versions of the dataset to which a record belongs.

        Parameters
        ----------
        rid
            The id of any published record of the dataset.

        Returns
        -------
        versions
            One record for every published version, in the order Zenodo returns them.
            Drafts are not included.
        """
        return self.get_all_pages(f"records/{rid}/versions")

    def get_user_records(self) -> list[dict[str, Any]]:
        """Get all records owned by the user of the token, published or not.

        Returns
        -------
        records
            The latest version of every dataset of the user, in the order Zenodo returns them.
        """
        return self.get_all_pages("user/records")

    def create_new_version(self, rid: str) -> dict[str, Any]:
        """Create a new version of a published record.

        The result is a draft record.
        """
        return self.rest.post(f"records/{rid}/versions")


NO_TOKEN_WARNING = """\
[yellow]The REPREP_ZENODO_TOKEN environment variable is not set.
Exiting early without interacting with the Zenodo endpoint.
Use --dry-run to validate the config file offline on purpose.[/yellow]
"""


def main(argv: Sequence[str] | None = None) -> int:
    """Main program.

    Returns
    -------
    returncode
        Zero when the synchronization succeeded,
        one when the user has to correct something or when Zenodo refused a request.
        The console script wrapper turns this into the exit status of the process.
    """
    args = _parse_args(argv)
    try:
        _run(args)
    except (ZenodoError, RESTError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except cattrs.BaseValidationError as exc:
        # Report what is wrong with each value instead of the nested exception group,
        # of which most frames sit in the structuring code that cattrs generates.
        for line in cattrs.transform_error(exc, repr(args.config), _format_error):
            print(line, file=sys.stderr)
        return 1
    return 0


def _run(args: argparse.Namespace):
    """Validate the configuration and synchronize the dataset with Zenodo."""
    try:
        paths = check_zenodo_paths(args.paths)
    except ValueError as exc:
        raise ZenodoError(str(exc)) from exc
    missing = [path for path in paths if not path.is_file()]
    if len(missing) > 0:
        raise ZenodoError(f"The following files to upload do not exist: {', '.join(missing)}.")
    data = _load_config_data(args.config)
    _check_outdated_config(data, args.config)
    config = _make_converter().structure(data, Config)

    if args.description is not None:
        if config.metadata.description is not None:
            raise ZenodoError(
                "The 'description' cannot be given twice. "
                "It is given in the config file and the --description command line argument."
            )
        config.metadata.description = _load_description(args.description)

    if args.dry_run:
        CONSOLE.print("[b]The following metadata would be sent to Zenodo:[/b]")
        CONSOLE.print(JSON.from_data(config.to_zenodo(paths)))
        return

    # The token is not tracked by StepUp to keep sensitive information out of the workflow graph.
    token = os.getenv("REPREP_ZENODO_TOKEN")
    if token is None:
        CONSOLE.print(NO_TOKEN_WARNING)
        return
    zenodo = ZenodoWrapper(token, config.endpoint, verbose=args.verbose)

    if args.clean:
        _clean_online(zenodo, config)
    _update_online(zenodo, config, paths)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="srr-sync-zenodo",
        description="Synchronize a draft dataset on Zenodo with your local files.",
    )
    parser.add_argument(
        "config",
        help=f"Configuration file. The format is selected by its suffix: {_format_suffixes()}.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="The files to upload to Zenodo. "
        "They must all have different names and there can be at most "
        f"{MAX_NUM_ZENODO_FILES} of them.",
    )
    parser.add_argument(
        "--description",
        help="A Markdown or HTML file describing the dataset. "
        "If not provided, the description will be taken from the config file. "
        "Markdown files are converted to HTML before uploading to Zenodo.",
    )
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
    parser.add_argument(
        "--dry-run",
        default=False,
        action="store_true",
        help="Validate the configuration, print the metadata that would be sent to Zenodo "
        "and exit without contacting Zenodo.",
    )
    return parser.parse_args(argv)


def _load_yaml(path: Path) -> Any:
    """Parse a YAML config file."""
    with open(path) as fh:
        return yaml.safe_load(fh)


def _load_json(path: Path) -> Any:
    """Parse a JSON config file."""
    with open(path) as fh:
        return json.load(fh)


def _load_toml(path: Path) -> Any:
    """Parse a TOML config file."""
    with open(path, "rb") as fh:
        return tomllib.load(fh)


CONFIG_LOADERS = {
    ".yaml": _load_yaml,
    ".yml": _load_yaml,
    ".json": _load_json,
    ".toml": _load_toml,
}
"""The parser to use for each config file suffix."""

LEGACY_ZENODO_JSON = ".zenodo.json"
"""The metadata file that Zenodo reads when it archives a GitHub release."""


def _format_suffixes() -> str:
    """Join the supported config file suffixes into a comma-separated list."""
    return ", ".join(sorted(CONFIG_LOADERS))


def _load_config_data(path: str | Path) -> dict[str, Any]:
    """Load the raw contents of a config file, selecting the parser by file name suffix.

    Parameters
    ----------
    path
        The config file to read.

    Returns
    -------
    data
        The mapping parsed from the file, not structured into a `Config` yet.
    """
    path = Path(path)
    if path.name == LEGACY_ZENODO_JSON:
        raise ZenodoError(
            f"{path} is not a srr-sync-zenodo configuration file. "
            f"A file named {LEGACY_ZENODO_JSON} holds the metadata that Zenodo reads "
            "when it archives a GitHub release, which follows a different schema. "
            "It is documented in the GitHub integration section of "
            "https://developers.zenodo.org/#github"
        )
    loader = CONFIG_LOADERS.get(path.suffix.lower())
    if loader is None:
        raise ZenodoError(
            f"Cannot derive the format of the config file {path} from its suffix. "
            f"The supported suffixes are {_format_suffixes()}."
        )
    try:
        data = loader(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ZenodoError(f"Cannot read the config file {path}: {exc}") from exc
    if data is None:
        raise ZenodoError(f"The config file {path} is empty.")
    if not isinstance(data, dict):
        raise ZenodoError(
            f"The config file {path} must hold a mapping of keys to values at the top level, "
            f"not a {type(data).__name__}."
        )
    return data


REPLACED_CONFIG_KEYS = {
    "paths": "Specify the files to upload as command line arguments instead.",
    "path_token": "Set the REPREP_ZENODO_TOKEN environment variable instead.",
    "path_readme": "Specify the description file with the --description option instead.",
    "code_repository": "Move it into the 'custom_fields' section.",
}
"""Keys that older config files may still contain, with a hint on how to replace them."""


def _check_outdated_config(data: dict[str, Any], config_path: str):
    """Raise an informative error when the config file still uses a key that was replaced."""
    for key, hint in REPLACED_CONFIG_KEYS.items():
        if key in data:
            raise ZenodoError(
                f"The config file {config_path} is outdated. "
                f"The '{key}' key is no longer used. {hint}"
            )


def _make_converter() -> cattrs.Converter:
    """Create the converter that structures the data of a config file into a `Config`."""
    converter = cattrs.Converter(forbid_extra_keys=True)
    converter.register_structure_hook(str, _structure_str)
    converter.register_structure_hook_func(lambda type_: type_ == list[str], _structure_list_str)
    converter.register_structure_hook_factory(attrs.has, _make_section_hook)
    converter.register_structure_hook_factory(_is_list_of_sections, _make_list_of_sections_hook)
    return converter


def _make_section_hook(type_: type, converter: cattrs.Converter) -> Callable:
    """Create a hook that structures a section of the config file into an attrs class.

    Parameters
    ----------
    type_
        The attrs class to structure into.
    converter
        The converter for which the hook is made.

    Returns
    -------
    hook
        A cattrs structuring hook rejecting a value that is not a mapping.
    """
    structure_mapping = make_dict_structure_fn(type_, converter)

    def structure(value: Any, type__: type) -> Any:
        if not isinstance(value, Mapping):
            raise TypeError(
                f"Expected a mapping of keys to values, got {type(value).__name__}: {value!r}."
            )
        return structure_mapping(value, type__)

    return structure


def _is_list_of_sections(type_: Any) -> bool:
    """Tell whether a type annotation describes a list of sections of the config file."""
    args = get_args(type_)
    return get_origin(type_) is list and len(args) == 1 and attrs.has(args[0])


def _make_list_of_sections_hook(type_: type, converter: cattrs.Converter) -> Callable:
    """Create a hook that structures a list of sections of the config file.

    Parameters
    ----------
    type_
        The list type to structure into, whose item type is an attrs class.
    converter
        The converter for which the hook is made.

    Returns
    -------
    hook
        A cattrs structuring hook rejecting a value that is not a list.
        A string is rejected too, even though it is a sequence,
        because it would otherwise be structured item by item, one error per character.
    """
    structure_list = list_structure_factory(type_, converter)

    def structure(value: Any, type__: type) -> Any:
        if isinstance(value, str) or not isinstance(value, Sequence):
            raise TypeError(f"Expected a list of mappings, got {type(value).__name__}: {value!r}.")
        return structure_list(value, type__)

    return structure


def _structure_str(value: Any, _type) -> str:
    """Structure a string without coercing other types.

    The default cattrs hook stringifies anything,
    which would silently accept an unquoted YAML value such as `version: 1.0`.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"Expected a string, got {type(value).__name__}: {value!r}. "
            "Enclose the value in quotes to make it a string."
        )
    return value


def _structure_list_str(value: Any, _type) -> list[str]:
    """Structure a list of strings, accepting a single string as a one element list.

    A string is itself an iterable of strings,
    so the default cattrs hook would turn `keywords: coffee` into a list of characters.
    """
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        return [_structure_str(item, str) for item in value]
    raise TypeError(
        f"Expected a string or a list of strings, got {type(value).__name__}: {value!r}."
    )


def _format_error(exc: BaseException, type_: type | None) -> str:
    """Format an error for `cattrs.transform_error`, keeping the message of a failed validation.

    Parameters
    ----------
    exc
        The exception raised while structuring one value.
    type_
        The type the value was structured into, if known.

    Returns
    -------
    message
        A description of what is wrong with the value.
    """
    if isinstance(exc, ValueError | TypeError) and len(exc.args) > 0:
        # Only the first argument holds the message.
        # The validators of attrs pass the attribute, the options and the value as well.
        return str(exc.args[0])
    return cattrs.v.format_exception(exc, type_)


def _load_description(path: str | Path) -> str:
    """Load the description from a Markdown or HTML file."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".md", ".html"):
        raise ZenodoError("The description file must be a Markdown (.md) or HTML (.html) file.")
    if not path.is_file():
        raise ZenodoError(f"Description file {path} does not exist.")
    with open(path) as fh:
        description = fh.read()
    if suffix == ".md":
        description = MarkdownIt().render(description)
    if len(description) < MIN_DESCRIPTION_LEN:
        raise ZenodoError(
            f"The description file {path} holds too little text. "
            f"Zenodo reads a description of at least {MIN_DESCRIPTION_LEN} characters."
        )
    return description


def _clean_online(zenodo: ZenodoWrapper, config: Config):
    """Remove all draft data sets on Zenodo."""
    for record in zenodo.get_user_records():
        rid = _record_id(record)
        if _is_published(record):
            CONSOLE.print(f"[yellow]Record {rid} is already published, skipping.[/yellow]")
            continue
        CONSOLE.print(f"Deleting draft record {rid}.")
        try:
            zenodo.rest.delete(f"records/{rid}/draft")
        except RESTError as exc:
            CONSOLE.print(f"[red]Failed to delete record {rid}: {exc}[/red]")
    config.path_record_id.remove_p()


def _update_online(zenodo: ZenodoWrapper, config: Config, paths: list[Path]):
    """Make the online data set up to date with the local information.

    Parameters
    ----------
    zenodo
        The Zenodo wrapper.
    config
        The configuration loaded from the config file.
    paths
        The files to upload to Zenodo, validated with `check_zenodo_paths`.
    """
    rid = None
    if config.path_record_id.exists():
        rid = config.path_record_id.read_text().strip()
        if len(rid) == 0:
            raise ZenodoError(f"The record ID file {config.path_record_id} is empty.")
    if rid is None:
        _upload_new_record(zenodo, config, paths)
    else:
        _refresh_existing_record(zenodo, rid, config, paths)


def _write_record_id(path: Path, rid: str):
    """Store the id of the record that the next run has to update."""
    with open(path, "w") as fh:
        fh.write(f"{rid}\n")


def _upload_new_record(zenodo: ZenodoWrapper, config: Config, paths: list[Path]):
    """Create a new record on Zenodo and upload the files to it.

    The record id is stored before the files are uploaded,
    so a failed upload leaves a draft that the next run completes,
    instead of an orphan that only `--clean` can remove.
    """
    record = zenodo.create_new_record(config, paths)
    rid = _record_id(record)
    _write_record_id(config.path_record_id, rid)
    CONSOLE.print(f"[b]New record:[/b] {_record_url(zenodo, record)}")

    # Declare the files to be uploaded.
    zenodo.start_uploads(rid, paths)

    # Actual uploads, one by one.
    for path in paths:
        CONSOLE.print(f"[green]Uploading:[/green] {path}")
        zenodo.upload_file(rid, path)
    if len(paths) > 0:
        # The metadata is sent again, now that the files exist,
        # so that Zenodo applies the order and the default preview to them.
        zenodo.update_metadata(rid, config, paths)


def _refresh_existing_record(zenodo: ZenodoWrapper, rid: str, config: Config, paths: list[Path]):
    """Refresh an existing record on Zenodo.

    The metadata is always sent again, without comparing it to what is online,
    because the API does not return all the metadata it accepts,
    as observed in June 2025.
    """
    # When a dataset exists, the actions depend on the current status of the record.
    record = zenodo.get_record(rid)
    CONSOLE.print(f"[b]Existing record:[/b] {_record_url(zenodo, record)}")

    named_paths = {path.name: path for path in paths}
    zenodo_version = _get_record_version(record)
    if _is_published(record):
        _check_version_chain(zenodo, record, config)
        if config.metadata.version == zenodo_version:
            _check_record_md5(record, named_paths, config.metadata.version)
            _republish_metadata(zenodo, rid, config, paths, _record_publication_date(record))
        else:
            record = _create_new_version(zenodo, rid, config)
            rid = _record_id(record)
            _write_record_id(config.path_record_id, rid)
            _refresh_draft(zenodo, rid, record, config, paths)
    else:
        _refresh_draft(zenodo, rid, record, config, paths)


def _refresh_draft(
    zenodo: ZenodoWrapper, rid: str, record: dict[str, Any], config: Config, paths: list[Path]
):
    """Bring the files and the metadata of a draft record up to date.

    The metadata is sent before and after the files are refreshed,
    because Zenodo only accepts an upload to a record whose metadata has enabled the files,
    and it only applies their order and default preview once they exist.

    Parameters
    ----------
    zenodo
        The Zenodo wrapper.
    rid
        The id of the draft record.
    record
        The draft record as returned by the Zenodo API.
    config
        The configuration loaded from the config file.
    paths
        The files to upload to Zenodo, validated with `check_zenodo_paths`.
    """
    CONSOLE.print("Updating metadata of draft record.")
    zenodo.update_metadata(rid, config, paths)
    named_paths = {path.name: path for path in paths}
    _refresh_files(zenodo, rid, record, named_paths, config.metadata.version)
    if len(paths) > 0:
        CONSOLE.print("Updating file order of draft record.")
        zenodo.update_metadata(rid, config, paths)


def _check_version_chain(zenodo: ZenodoWrapper, record: dict[str, Any], config: Config):
    """Check a published record against the other published versions of the same dataset.

    Zenodo stores the version as free text and never orders versions by it,
    so the version chain on Zenodo is the only thing that can tell
    a new version from a stale checkout or a revert.

    Parameters
    ----------
    zenodo
        The Zenodo wrapper.
    record
        The published record whose id is stored in the local record id file.
    config
        The configuration loaded from the config file.

    Raises
    ------
    ZenodoError
        When the record is not the latest published version of the dataset,
        or when the local version is already published as another version.
    """
    rid = _record_id(record)
    version = config.metadata.version
    latest = None
    taken = None
    for other in zenodo.get_versions(rid):
        if other.get("versions", {}).get("is_latest", False):
            latest = other
        if _record_id(other) != rid and _get_record_version(other) == version:
            taken = other
    if latest is None:
        raise ZenodoError(
            f"Zenodo did not mark any published version of record {rid} as the latest one. "
            f"The Accept header of this module, {INVENIORDM_MIMETYPE}, may no longer be honored."
        )
    if _record_id(latest) != rid:
        raise ZenodoError(
            f"Record {rid} ({_describe_version(record)}) "
            "is not the latest published version of this dataset. "
            f"That is record {_record_id(latest)} ({_describe_version(latest)}). "
            f"Update {config.path_record_id} and the version in the config file, "
            "e.g. by pulling in the work of your collaborators."
        )
    if taken is not None:
        raise ZenodoError(
            f"Version {version} is already published as record {_record_id(taken)} of "
            f"this dataset, while the latest published version has {_describe_version(latest)}. "
            "Put a version in the config file that was not published before."
        )


def _compute_md5(path: Path) -> str:
    """Compute the MD5 sum of a local file, as a hexadecimal string."""
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, hashlib.md5).hexdigest()


def _entry_md5(entry: dict[str, Any]) -> str:
    """Extract the MD5 sum that Zenodo computed for a file, as a hexadecimal string.

    Parameters
    ----------
    entry
        The file entry of a record, or the response to the commit of an upload.

    Returns
    -------
    md5
        The hexadecimal digest, without the name of the algorithm.

    Raises
    ------
    ZenodoError
        When Zenodo used another algorithm, whose digest cannot be compared to a local MD5 sum.
    """
    checksum = entry.get("checksum")
    if not (isinstance(checksum, str) and checksum.startswith(MD5_PREFIX)):
        raise ZenodoError(f"Zenodo returned an unexpected checksum format: {checksum!r}")
    return checksum[len(MD5_PREFIX) :]


def _search_hits(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract the records from one page of a search result.

    Parameters
    ----------
    data
        A search result as returned by the Zenodo API.

    Returns
    -------
    hits
        The records on the requested page.
    """
    hits = data.get("hits")
    if not (isinstance(hits, dict) and isinstance(hits.get("hits"), list)):
        raise ZenodoError(
            "Zenodo did not describe a search result as an object with a list of hits. "
            f"The Accept header of this module, {INVENIORDM_MIMETYPE}, may no longer be honored."
        )
    return hits["hits"]


def _get_record_version(record: dict[str, Any]) -> str | None:
    """Extract the version of a record.

    Zenodo does not require a version,
    so a record made outside of `srr-sync-zenodo` may well carry none.

    Parameters
    ----------
    record
        A record as returned by the Zenodo API.

    Returns
    -------
    version
        The version Zenodo stored, or `None` when the record has none.
    """
    return record.get("metadata", {}).get("version")


def _is_published(record: dict[str, Any]) -> bool:
    """Tell whether a record is published, as opposed to a draft that was never published.

    Parameters
    ----------
    record
        A record as returned by the Zenodo API.

    Returns
    -------
    is_published
        Whether the record is published.

    Raises
    ------
    ZenodoError
        When the record does not say, because acting on a guess would either
        delete a record or try to change the files of a published one.
    """
    is_published = record.get("is_published")
    if not isinstance(is_published, bool):
        raise ZenodoError(
            f"Zenodo did not say whether record {record.get('id')} is published. "
            f"The Accept header of this module, {INVENIORDM_MIMETYPE}, may no longer be honored."
        )
    return is_published


def _record_publication_date(record: dict[str, Any]) -> str | None:
    """Extract the publication date of a record.

    Parameters
    ----------
    record
        A record as returned by the Zenodo API.

    Returns
    -------
    publication_date
        The publication date Zenodo stored, in ISO format,
        or `None` when the record has none.
    """
    return record.get("metadata", {}).get("publication_date")


def _record_id(record: dict[str, Any]) -> str:
    """Extract the id of a record.

    Parameters
    ----------
    record
        A record as returned by the Zenodo API.

    Returns
    -------
    rid
        The id of the record, as the string that identifies it in an address.

    Raises
    ------
    ZenodoError
        When the record does not carry an id.
    """
    rid = record.get("id")
    if rid is None:
        raise ZenodoError(
            "Zenodo did not send the id of a record. "
            f"The Accept header of this module, {INVENIORDM_MIMETYPE}, may no longer be honored."
        )
    return str(rid)


def _record_url(zenodo: ZenodoWrapper, record: dict[str, Any]) -> str:
    """Build the address of a record to show to the user.

    Parameters
    ----------
    zenodo
        The Zenodo wrapper.
    record
        A record as returned by the Zenodo API.

    Returns
    -------
    url
        The address of the record on the website of Zenodo,
        or its address in the API when Zenodo did not send one.
    """
    url = record.get("links", {}).get("self_html")
    return f"{zenodo.endpoint}/records/{_record_id(record)}" if url is None else url


def _describe_version(record: dict[str, Any]) -> str:
    """Describe the version of a record for use in an error message."""
    version = _get_record_version(record)
    return "no version" if version is None else f"version {version}"


def _get_record_files(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract the file entries of a record.

    Parameters
    ----------
    record
        A record as returned by the Zenodo API.

    Returns
    -------
    entries
        The file entry of every file in the record, keyed by file name.
        Each entry holds at least a `key`, a `checksum` and a `size`.
    """
    files = record.get("files")
    if not isinstance(files, dict):
        raise ZenodoError(
            "Zenodo did not describe the files of a record as an object with entries. "
            f"It sent a {type(files).__name__} instead. "
            f"The Accept header of this module, {INVENIORDM_MIMETYPE}, may no longer be honored."
        )
    return files.get("entries", {})


PUBLISHED_FILE_MISMATCH_HINT = (
    "The files of a published version cannot be changed. "
    "Put a version in the config file that was not published before, "
    "so that the local files are deposited as a new version."
)


def _check_record_md5(record: dict[str, Any], paths: dict[str, Path], version: str):
    """Check that the files of a published record are identical to the local ones.

    Parameters
    ----------
    record
        The published record as returned by the Zenodo API.
    paths
        The files to upload to Zenodo, keyed by file name.
    version
        The version of the dataset, used in the messages.

    Raises
    ------
    ZenodoError
        When a file exists on only one side, or when two files with the same name differ.
    """
    entries = _get_record_files(record)
    for name, entry in entries.items():
        CONSOLE.print(f"[cyan]Checking MD5:[/cyan] {name} ({version}, published)")
        if name not in paths:
            raise ZenodoError(
                f"File {name} exists online but not locally ({version}, published). "
                f"{PUBLISHED_FILE_MISMATCH_HINT}"
            )
        path = paths[name]
        local_md5 = _compute_md5(path)
        online_md5 = _entry_md5(entry)
        if local_md5 != online_md5:
            raise ZenodoError(
                f"MD5 checksum mismatch for {path} ({version}, published), "
                f"local: {local_md5}, online: {online_md5}. {PUBLISHED_FILE_MISMATCH_HINT}"
            )
    for name in paths:
        if name not in entries:
            raise ZenodoError(
                f"File {name} exists locally but not online ({version}, published). "
                f"{PUBLISHED_FILE_MISMATCH_HINT}"
            )


def _republish_metadata(
    zenodo: ZenodoWrapper, rid: str, config: Config, paths: list[Path], publication_date: str | None
):
    """Put a record in edit mode, update the metadata and publish again.

    The publication date of the record is preserved,
    because this version was published on that date, not today.
    """
    CONSOLE.print(
        f"Editing metadata and publishing same version ({config.metadata.version}) again."
    )
    zenodo.edit_record(rid)
    zenodo.update_metadata(rid, config, paths, publication_date)
    zenodo.publish_record(rid)


def _create_new_version(zenodo: ZenodoWrapper, rid: str, config: Config) -> dict[str, Any]:
    """Create a new version of the dataset."""
    CONSOLE.print(f"Creating a new version ({config.metadata.version})")
    return zenodo.create_new_version(rid)


def _refresh_files(
    zenodo: ZenodoWrapper,
    rid: str,
    record: dict[str, Any],
    paths: dict[str, Path],
    version: str,
):
    """Refresh the online files.

    Only files that do not exist online yet or have changed locally are uploaded.
    Files that are no longer listed locally are removed online.

    Parameters
    ----------
    zenodo
        The Zenodo wrapper.
    rid
        The id of the draft record.
    record
        The draft record as returned by the Zenodo API.
    paths
        The files to upload to Zenodo, keyed by file name.
    version
        The version of the dataset, used in the messages.
    """
    entries = _get_record_files(record)
    for name, entry in entries.items():
        if name not in paths:
            CONSOLE.print(f"[red]Deleting:[/red] {name} ({version}, draft)")
            zenodo.delete_file(rid, name)
        else:
            path = paths[name]
            if _compute_md5(path) != _entry_md5(entry):
                CONSOLE.print(f"[yellow]Replacing:[/yellow] {path} ({version}, draft)")
                zenodo.delete_file(rid, name)
                zenodo.start_uploads(rid, [path])
                zenodo.upload_file(rid, path)
            else:
                CONSOLE.print(f"[cyan]Same MD5:[/cyan] {path} ({version}, draft)")
    for name, path in paths.items():
        if name not in entries:
            CONSOLE.print(f"[green]Uploading:[/green] {path} ({version}, draft)")
            zenodo.start_uploads(rid, [path])
            zenodo.upload_file(rid, path)


if __name__ == "__main__":
    sys.exit(main())
