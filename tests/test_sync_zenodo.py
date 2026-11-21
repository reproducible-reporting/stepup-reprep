# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.sync_zenodo."""

import datetime as dt
import hashlib
import json
from importlib import resources
from urllib.parse import unquote

import cattrs
import pytest
import requests
import yaml
from cattrs.errors import ClassValidationError
from reprep_common import needs_symlinks

import stepup.core.api
from stepup.core.exceptions import InputNotFoundError
from stepup.core.path import Path
from stepup.reprep.inventory import FileRecord, InventoryHeader, format_header, format_record
from stepup.reprep.make_inventory import write_inventory
from stepup.reprep.sync_zenodo import (
    DEFAULT_ENDPOINT,
    INVENIORDM_MIMETYPE,
    MAX_NUM_ZENODO_FILES,
    MAX_SEARCH_PAGES,
    REPLACED_CONFIG_KEYS,
    REQUEST_TIMEOUT,
    SEARCH_PAGE_SIZE,
    VOCABULARIES_FILENAME,
    Access,
    Award,
    Config,
    Creator,
    CustomFields,
    FileDiff,
    Funding,
    Identifier,
    Imprint,
    Journal,
    Meeting,
    Metadata,
    Organization,
    Related,
    RESTError,
    RESTWrapper,
    Thesis,
    UploadFile,
    ZenodoError,
    ZenodoWrapper,
    _check_draft_errors,
    _check_outdated_config,
    _check_record_md5,
    _check_version_chain,
    _check_zenodo_limits,
    _describe_version,
    _diff_files,
    _entry_md5,
    _file_loc,
    _format_error,
    _get_record_files,
    _get_record_version,
    _is_published,
    _load_config_data,
    _load_vocabularies,
    _make_converter,
    _parse_args,
    _record_id,
    _record_publication_date,
    _record_url,
    _refresh_draft,
    _refresh_existing_record,
    _refresh_files,
    _search_hits,
    _update_online,
    _upload_new_record,
    _write_record_id,
    main,
)


@pytest.mark.parametrize(
    "orcid",
    ["0000-0001-9288-5608", "0000-0001-6785-333X", "0000-0001-6785-333x", "0000-0002-0257-4687"],
)
def test_creator_orcid_valid(orcid):
    Creator("Test User", "StepUp RepRep", {"orcid": orcid})


@pytest.mark.parametrize(
    "orcid",
    [
        "0000-0002-0257-4687  0000-0002-0257-46870000-0001-9288-560x",
        "0000-0001-9288-560X",
        "0000-0001-6785-3337",
        "0000-0002-1825-009",
        "0000-0002-1825-00977",
        "000-0002-1825-0097",
        "0000X0002-1825-0097",
        "https://orcid.org/0000-0002-1825-0097",
        "ABCD-EFGH-IJKL-MNOP",
        "1234-5678-9012-345y",
        "",
        "    ",
        "0000-0002-1825-0090",
        "0000-0002-1694-233A",
    ],
)
def test_creator_orcid_invalid(orcid):
    with pytest.raises(ValueError):
        Creator("Test User", "StepUp RepRep", {"orcid": orcid})


@pytest.mark.parametrize("scheme", ["ORCID", "gnd", "ror", ""])
def test_creator_identifier_scheme_unknown(scheme):
    with pytest.raises(ValueError, match="Unknown identifier scheme for 'identifiers'"):
        Creator("Test User", "StepUp RepRep", {scheme: "0000-0001-9288-5608"})


def test_creator_orcid_message_names_the_attribute():
    """The error surfaces at the creator, so the message has to say which field is wrong."""
    with pytest.raises(ValueError, match="Invalid ORCID for 'identifiers'"):
        Creator("Test User", identifiers={"orcid": "https://orcid.org/0000-0001-9288-5608"})


@pytest.mark.parametrize("isni", ["0000 0001 6785 333X", "0000000016785333"])
def test_creator_isni_valid(isni):
    Creator("Test User", identifiers={"isni": isni})


@pytest.mark.parametrize(
    "isni",
    ["https://isni.org/isni/0000000016785333", "0000 0001 6785 3330", "abc", ""],
)
def test_creator_isni_invalid(isni):
    with pytest.raises(ValueError, match="Invalid ISNI for 'identifiers'"):
        Creator("Test User", identifiers={"isni": isni})


def test_custom_fields_to_zenodo():
    custom_fields = CustomFields(
        code_repository="https://github.com/reproducible-reporting/stepup-reprep",
        development_status="active",
        programming_languages=["python", "jupyter_notebook"],
    )
    assert custom_fields.to_zenodo() == {
        "code:codeRepository": "https://github.com/reproducible-reporting/stepup-reprep",
        "code:developmentStatus": {"id": "active"},
        "code:programmingLanguage": [{"id": "python"}, {"id": "jupyter_notebook"}],
    }


def test_custom_fields_to_zenodo_unset():
    assert CustomFields().to_zenodo() == {}
    assert CustomFields(development_status="wip").to_zenodo() == {
        "code:developmentStatus": {"id": "wip"}
    }


def test_custom_fields_structure():
    data = {
        "code_repository": "https://example.org/repo",
        "development_status": "concept",
        "programming_languages": ["fortran"],
    }
    custom_fields = _make_converter().structure(data, CustomFields)
    assert custom_fields == CustomFields("https://example.org/repo", "concept", ["fortran"])


def test_custom_fields_structure_zenodo_name():
    """The config file uses the intuitive names, not the ones from Zenodo's API."""
    data = {"code:codeRepository": "https://example.org/repo"}
    with pytest.raises(ClassValidationError):
        _make_converter().structure(data, CustomFields)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/example/repo",
        "http://example.org",
        "ftp://example.org/repo.git",
        "https://localhost:8080/repo",
        "http://localhost:8080/x",
        "https://127.0.0.1/x",
        "https://[2001:db8::1]/x",
        "ftp://example.co.uk",
        "https://user:pw@example.org/a?b=c",
    ],
)
def test_custom_fields_code_repository_valid(url):
    assert CustomFields(code_repository=url).code_repository == url


@pytest.mark.parametrize(
    "url",
    [
        "github.com/example/repo",
        "https://example",
        "git@github.com:example/repo.git",
        "",
        "http://foo",
        "example.org/x",
        "mailto:a@b.org",
        "https://",
        "https://example.x",
    ],
)
def test_custom_fields_code_repository_invalid(url):
    with pytest.raises(ValueError):
        CustomFields(code_repository=url)


@pytest.mark.parametrize("identifier", ["Active", "unknown", "ACTIVE", ""])
def test_custom_fields_development_status_invalid(identifier):
    with pytest.raises(ValueError):
        CustomFields(development_status=identifier)


@pytest.mark.parametrize("identifier", ["Python", "pythonic", "C++ "])
def test_custom_fields_programming_languages_invalid(identifier):
    with pytest.raises(ValueError):
        CustomFields(programming_languages=["python", identifier])


def test_custom_fields_structure_scalar():
    """A single value is accepted where a list of strings belongs."""
    data = {"programming_languages": "python"}
    custom_fields = _make_converter().structure(data, CustomFields)
    assert custom_fields.programming_languages == ["python"]


def test_custom_fields_structure_scalar_not_a_string():
    data = {"programming_languages": 3}
    with pytest.raises(ClassValidationError) as exc_info:
        _make_converter().structure(data, CustomFields)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any("Expected a string or a list of strings, got int" in msg for msg in messages)


def test_custom_fields_structure_list_item_not_a_string():
    data = {"programming_languages": ["python", 3]}
    with pytest.raises(ClassValidationError) as exc_info:
        _make_converter().structure(data, CustomFields)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any("Expected a string, got int" in msg for msg in messages)


def test_custom_fields_rights_holder_to_zenodo():
    custom_fields = CustomFields(rights_holder=["Ghent University", "KU Leuven"])
    assert custom_fields.to_zenodo() == {"dc:rightsHolder": ["Ghent University", "KU Leuven"]}


def test_custom_fields_journal_to_zenodo():
    journal = Journal(
        title="Journal of Chemical Physics",
        issue="3",
        volume="42",
        pages="123-145",
        issn="0378-5955",
    )
    assert CustomFields(journal=journal).to_zenodo() == {
        "journal:journal": {
            "title": "Journal of Chemical Physics",
            "issue": "3",
            "volume": "42",
            "pages": "123-145",
            "issn": "0378-5955",
        }
    }


def test_custom_fields_meeting_to_zenodo():
    meeting = Meeting(
        title="International Conference on Coffee",
        acronym="ICC24",
        dates="1-3 June 2024",
        place="Ghent, Belgium",
        session="VI",
        session_part="1",
        url="https://example.org/icc24",
        identifiers=[
            Identifier("10.5281/zenodo.1234567", "doi"),
            Identifier("https://example.org/icc24/proceedings"),
        ],
    )
    assert CustomFields(meeting=meeting).to_zenodo() == {
        "meeting:meeting": {
            "title": "International Conference on Coffee",
            "acronym": "ICC24",
            "dates": "1-3 June 2024",
            "place": "Ghent, Belgium",
            "session": "VI",
            "session_part": "1",
            "url": "https://example.org/icc24",
            "identifiers": [
                {"scheme": "doi", "identifier": "10.5281/zenodo.1234567"},
                {"identifier": "https://example.org/icc24/proceedings"},
            ],
        }
    }


def test_custom_fields_imprint_to_zenodo():
    imprint = Imprint(
        title="Handbook of Coffee",
        isbn="978-3-16-148410-0",
        pages="15-30",
        place="Ghent, Belgium",
        edition="2nd",
    )
    assert CustomFields(imprint=imprint).to_zenodo() == {
        "imprint:imprint": {
            "title": "Handbook of Coffee",
            "isbn": "978-3-16-148410-0",
            "pages": "15-30",
            "place": "Ghent, Belgium",
            "edition": "2nd",
        }
    }


def test_custom_fields_thesis_to_zenodo():
    thesis = Thesis(
        university="Ghent University",
        department="Center for Molecular Modeling",
        type="PhD",
        date_submitted="2024-06-15",
        date_defended="2024-09-23",
    )
    assert CustomFields(thesis=thesis).to_zenodo() == {
        "thesis:thesis": {
            "university": "Ghent University",
            "department": "Center for Molecular Modeling",
            "type": "PhD",
            "date_submitted": "2024-06-15",
            "date_defended": "2024-09-23",
        }
    }


def test_custom_fields_nested_partially_unset():
    """The keys that are not set stay out of the nested object."""
    custom_fields = CustomFields(journal=Journal(title="Journal of Coffee"))
    assert custom_fields.to_zenodo() == {"journal:journal": {"title": "Journal of Coffee"}}


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("journal", Journal()),
        ("meeting", Meeting()),
        ("imprint", Imprint()),
        ("thesis", Thesis()),
    ],
)
def test_custom_fields_nested_all_unset(name, value):
    """An object without a single key set is not sent to Zenodo."""
    assert CustomFields(**{name: value}).to_zenodo() == {}


CUSTOM_FIELDS_DATA = {
    "rights_holder": "Ghent University",
    "journal": {"title": "Journal of Coffee", "issn": "0378-5955"},
    "meeting": {
        "acronym": "ICC24",
        "url": "https://example.org/icc24",
        "identifiers": [{"scheme": "doi", "identifier": "10.5281/zenodo.1234567"}],
    },
    "imprint": {"title": "Handbook of Coffee", "isbn": "978-3-16-148410-0"},
    "thesis": {"university": "Ghent University", "date_defended": "2024-09-23"},
}


def test_custom_fields_structure_nested():
    """The nested custom fields are structured from the intuitive config keys."""
    custom_fields = _make_converter().structure(CUSTOM_FIELDS_DATA, CustomFields)
    assert custom_fields == CustomFields(
        rights_holder=["Ghent University"],
        journal=Journal(title="Journal of Coffee", issn="0378-5955"),
        meeting=Meeting(
            acronym="ICC24",
            url="https://example.org/icc24",
            identifiers=[Identifier("10.5281/zenodo.1234567", "doi")],
        ),
        imprint=Imprint(title="Handbook of Coffee", isbn="978-3-16-148410-0"),
        thesis=Thesis(university="Ghent University", date_defended="2024-09-23"),
    )


@pytest.mark.parametrize("issn", ["1234-5678", "0378-595X", "0378-5955-1", "abc", ""])
def test_custom_fields_journal_issn_invalid(issn):
    with pytest.raises(ValueError):
        Journal(issn=issn)


@pytest.mark.parametrize("isbn", ["978-3-16-148410-1", "030640615X", "abc", ""])
def test_custom_fields_imprint_isbn_invalid(isbn):
    with pytest.raises(ValueError):
        Imprint(isbn=isbn)


@pytest.mark.parametrize("url", ["example.org/icc24", "https://example", "", "mailto:a@b.org"])
def test_custom_fields_meeting_url_invalid(url):
    with pytest.raises(ValueError):
        Meeting(url=url)


@pytest.mark.parametrize("scheme", ["DOI", "orcid", "unknown", ""])
def test_custom_fields_meeting_identifier_scheme_invalid(scheme):
    with pytest.raises(ValueError):
        Identifier("10.5281/zenodo.1234567", scheme)


def test_custom_fields_meeting_identifier_scheme_mismatch():
    with pytest.raises(ValueError):
        Identifier("not a doi", "doi")


@pytest.mark.parametrize("date", ["2024-13-01", "2024-02-30", "2024-00", "0000"])
def test_custom_fields_thesis_date_impossible(date):
    with pytest.raises(ValueError):
        Thesis(date_submitted=date)
    with pytest.raises(ValueError):
        Thesis(date_defended=date)


@pytest.mark.parametrize("date", ["1984~", "1984-06-uu", "2024?", "2024-06", "2024", "2024/2025"])
def test_custom_fields_thesis_date_edtf(date):
    """A date that is not a plain calendar date is left for Zenodo to judge."""
    assert Thesis(date_submitted=date).date_submitted == date


def test_custom_fields_nested_error_message():
    """A failure inside a nested object names the key that holds it."""
    data = {"journal": {"issn": "1234-5678"}}
    with pytest.raises(ClassValidationError) as exc_info:
        _make_converter().structure(data, CustomFields)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any(
        "Invalid ISSN for 'issn'" in message and "$.journal" in message for message in messages
    )


@pytest.mark.parametrize(
    "kwargs",
    [{"id": "00k4n6c32::101052382"}, {"title": "A title"}, {"number": "GN23549"}],
)
def test_award_known_or_free_text(kwargs):
    """Zenodo takes an award it already knows, or a free text title, or a free text number."""
    assert Funding(Organization(ror="00cv9y106"), Award(**kwargs)).to_zenodo()["award"] != {}


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"id": "00k4n6c32::101052382", "title": "A title"},
        {"id": "00k4n6c32::101052382", "number": "1"},
    ],
)
def test_award_neither_or_both(kwargs):
    """An award without any description is refused, and so is free text next to an id."""
    with pytest.raises(ValueError) as exc_info:
        Award(**kwargs)
    assert "either by 'id'" in str(exc_info.value)


VOCABULARY_NAMES = [
    "code:developmentStatus",
    "code:programmingLanguages",
    "languages",
    "licenses",
    "relationtypes",
    "resourcetypes",
]


def test_load_vocabularies():
    vocabularies = _load_vocabularies()
    assert sorted(vocabularies) == VOCABULARY_NAMES
    assert all(len(vocabularies[name]) > 0 for name in VOCABULARY_NAMES)


def test_load_vocabularies_without_bookkeeping():
    """The date of the last refresh is not an identifier that Zenodo takes."""
    text = (
        resources.files("stepup.reprep").joinpath(VOCABULARIES_FILENAME).read_text(encoding="utf-8")
    )
    assert "_date" in yaml.safe_load(text)
    assert "_date" not in _load_vocabularies()


@pytest.mark.parametrize("name", VOCABULARY_NAMES)
def test_vocabularies_data_file_sorted_and_unique(name):
    """Guard against a hand edit that the refresh script would have prevented."""
    text = (
        resources.files("stepup.reprep").joinpath(VOCABULARIES_FILENAME).read_text(encoding="utf-8")
    )
    identifiers = yaml.safe_load(text)[name]
    assert all(isinstance(identifier, str) for identifier in identifiers)
    assert identifiers == sorted(set(identifiers))


DESCRIPTION = "<p>A dataset.</p>\n"
"""A description in HTML, as `srr-sync-zenodo` sends it to Zenodo."""


def _metadata(**kwargs) -> Metadata:
    kwargs.setdefault("title", "A title")
    kwargs.setdefault("version", "1.0.0")
    kwargs.setdefault("creators", [Creator("Verstraelen", "Toon")])
    kwargs.setdefault("publisher", "Zenodo")
    return Metadata(**kwargs)


@pytest.mark.parametrize("identifier", ["dataset", "software", "publication-article"])
def test_metadata_resource_type_valid(identifier):
    metadata = _metadata(license=["cc-by-4.0"], resource_type=identifier)
    assert metadata.to_zenodo(DESCRIPTION)["resource_type"] == {"id": identifier}


@pytest.mark.parametrize("identifier", ["Dataset", "DATASET", "datasets", "audio", ""])
def test_metadata_resource_type_invalid(identifier):
    with pytest.raises(ValueError):
        _metadata(license=["cc-by-4.0"], resource_type=identifier)


@pytest.mark.parametrize("identifier", ["cc-by-4.0", "cc-by-nc-4.0", "mit", "CC-BY-4.0"])
def test_metadata_license_valid(identifier):
    """The license is lowercased before it is validated."""
    metadata = _metadata(license=[identifier], resource_type="dataset")
    assert metadata.to_zenodo(DESCRIPTION)["rights"] == [{"id": identifier.lower()}]


@pytest.mark.parametrize("identifier", ["cc-by-4", "cc by 4.0", "gfdl", ""])
def test_metadata_license_invalid(identifier):
    with pytest.raises(ValueError):
        _metadata(license=[identifier], resource_type="dataset")


def _related(**kwargs) -> Related:
    kwargs.setdefault("scheme", "doi")
    kwargs.setdefault("identifier", "10.5281/zenodo.1234567")
    return Related(**kwargs)


@pytest.mark.parametrize("identifier", ["cites", "issupplementto", "isversionof"])
def test_related_relation_type_valid(identifier):
    related = _related(relation_type=identifier)
    assert related.to_zenodo()["relation_type"] == {"id": identifier}


@pytest.mark.parametrize("identifier", ["Cites", "CITES", "cited", ""])
def test_related_relation_type_invalid(identifier):
    with pytest.raises(ValueError):
        _related(relation_type=identifier)


@pytest.mark.parametrize("identifier", ["Publication", "publication-thesis", ""])
def test_related_resource_type_invalid(identifier):
    with pytest.raises(ValueError):
        _related(relation_type="cites", resource_type=identifier)


def test_parse_args_minimal():
    args = _parse_args(["sync_zenodo.yaml", "zenodo_description.md", "zenodo_inventory.jsonl"])
    assert args.config == "sync_zenodo.yaml"
    assert args.description == "zenodo_description.md"
    assert args.inventory == "zenodo_inventory.jsonl"
    assert args.verbose is False
    assert args.dry_run is False
    assert args.no_check_md5 is False


def test_parse_args_all():
    args = _parse_args(
        [
            "sync_zenodo.toml",
            "zenodo_description.html",
            "zenodo_inventory.jsonl",
            "--verbose",
            "--dry-run",
            "--no-check-md5",
        ]
    )
    assert args.config == "sync_zenodo.toml"
    assert args.description == "zenodo_description.html"
    assert args.inventory == "zenodo_inventory.jsonl"
    assert args.verbose is True
    assert args.dry_run is True
    assert args.no_check_md5 is True


CONFIG_YAML = """\
path_record_id: .zenodo-record-id.txt
endpoint: https://zenodo.org/api
metadata:
  title: 'A title'
  version: '1.0.0'
  license: cc-by-4.0
  resource_type: dataset
  publisher: Zenodo
  creators:
    - family_name: Verstraelen
      given_name: Toon
      identifiers:
        orcid: '0000-0001-9288-5608'
      affiliations:
        - name: Ghent University
  funding:
    - funder:
        ror: 00cv9y106
      award:
        title: 'Title of the award'
        number: 'GN23549'
custom_fields:
  code_repository: https://github.com/example/repo
  development_status: active
  programming_languages:
    - python
    - jupyter_notebook
"""

CONFIG_JSON = """\
{
  "path_record_id": ".zenodo-record-id.txt",
  "endpoint": "https://zenodo.org/api",
  "metadata": {
    "title": "A title",
    "version": "1.0.0",
    "license": "cc-by-4.0",
    "resource_type": "dataset",
    "publisher": "Zenodo",
    "creators": [
      {
        "family_name": "Verstraelen",
        "given_name": "Toon",
        "identifiers": {"orcid": "0000-0001-9288-5608"},
        "affiliations": [{"name": "Ghent University"}]
      }
    ],
    "funding": [
      {
        "funder": {"ror": "00cv9y106"},
        "award": {"title": "Title of the award", "number": "GN23549"}
      }
    ]
  },
  "custom_fields": {
    "code_repository": "https://github.com/example/repo",
    "development_status": "active",
    "programming_languages": ["python", "jupyter_notebook"]
  }
}
"""

CONFIG_TOML = """\
path_record_id = ".zenodo-record-id.txt"
endpoint = "https://zenodo.org/api"

[metadata]
title = "A title"
version = "1.0.0"
license = "cc-by-4.0"
resource_type = "dataset"
publisher = "Zenodo"

[[metadata.creators]]
family_name = "Verstraelen"
given_name = "Toon"
identifiers = {orcid = "0000-0001-9288-5608"}
affiliations = [{name = "Ghent University"}]

[[metadata.funding]]
funder = {ror = "00cv9y106"}
award = {title = "Title of the award", number = "GN23549"}

[custom_fields]
code_repository = "https://github.com/example/repo"
development_status = "active"
programming_languages = ["python", "jupyter_notebook"]
"""


def _write_config(tmp_path, name: str, text: str) -> Config:
    """Write a config file in `tmp_path` and load it into a `Config`."""
    path = tmp_path / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return _make_converter().structure(_load_config_data(path), Config)


def test_config_formats_equivalent(tmp_path):
    """The same configuration in YAML, JSON and TOML produces the same Zenodo payload."""
    configs = [
        _write_config(tmp_path, "sync_zenodo.yaml", CONFIG_YAML),
        _write_config(tmp_path, "sync_zenodo.json", CONFIG_JSON),
        _write_config(tmp_path, "sync_zenodo.toml", CONFIG_TOML),
    ]
    payloads = [config.to_zenodo(DESCRIPTION, []) for config in configs]
    assert payloads[0] == payloads[1]
    assert payloads[0] == payloads[2]
    assert payloads[0]["metadata"]["version"] == "1.0.0"
    assert len(payloads[0]["metadata"]["creators"]) == 1
    assert payloads[0]["custom_fields"]["code:programmingLanguage"] == [
        {"id": "python"},
        {"id": "jupyter_notebook"},
    ]


def test_config_yml_suffix(tmp_path):
    config = _write_config(tmp_path, "sync_zenodo.yml", CONFIG_YAML)
    assert config.endpoint == "https://zenodo.org/api"


def test_config_toml_unquoted_date(tmp_path):
    """A bare TOML date is rejected just like an unquoted YAML version number."""
    text = CONFIG_TOML.replace('version = "1.0.0"', "version = 2024-01-01")
    path = tmp_path / "sync_zenodo.toml"
    path.write_text(text, encoding="utf-8", newline="\n")
    with pytest.raises(ClassValidationError) as exc_info:
        _make_converter().structure(_load_config_data(path), Config)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any("Enclose the value in quotes" in message for message in messages)


def test_load_config_data_unknown_suffix(tmp_path):
    path = tmp_path / "sync_zenodo.ini"
    path.write_text("[metadata]\n", encoding="utf-8", newline="\n")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "suffix" in str(exc_info.value)
    assert ".toml" in str(exc_info.value)


def test_load_config_data_legacy_zenodo_json(tmp_path):
    path = tmp_path / ".zenodo.json"
    path.write_text('{"title": "A title"}\n', encoding="utf-8", newline="\n")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "GitHub release" in str(exc_info.value)


def test_load_config_data_not_a_mapping(tmp_path):
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8", newline="\n")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "mapping" in str(exc_info.value)


def test_load_config_data_syntax_error(tmp_path):
    """A config file the parser chokes on is reported without the traceback of the parser."""
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text("metadata: [unclosed\n", encoding="utf-8", newline="\n")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "Cannot read the config file" in str(exc_info.value)


def test_load_config_data_missing(tmp_path):
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(tmp_path / "absent.yaml")
    assert "Cannot read the config file" in str(exc_info.value)


def test_load_config_data_empty(tmp_path):
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text("", encoding="utf-8", newline="\n")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "empty" in str(exc_info.value)


def test_config_endpoint_default(tmp_path):
    text = CONFIG_YAML.replace("endpoint: https://zenodo.org/api\n", "")
    config = _write_config(tmp_path, "sync_zenodo.yaml", text)
    assert config.endpoint == DEFAULT_ENDPOINT


@pytest.mark.parametrize("endpoint", ["zenodo.org/api", "https://zenodo", ""])
def test_config_endpoint_invalid(tmp_path, endpoint):
    text = CONFIG_YAML.replace("endpoint: https://zenodo.org/api", f"endpoint: '{endpoint}'")
    with pytest.raises(ClassValidationError):
        _write_config(tmp_path, "sync_zenodo.yaml", text)


@pytest.mark.parametrize("key", REPLACED_CONFIG_KEYS)
def test_config_replaced_key(tmp_path, key):
    """A key that an older release supported is reported with a hint, not as an unknown key."""
    data = yaml.safe_load(CONFIG_YAML)
    *sections, name = key.split(".")
    section = data
    for section_name in sections:
        section = section.setdefault(section_name, {})
    section[name] = "whatever"
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8", newline="\n")
    with pytest.raises(ZenodoError) as exc_info:
        _check_outdated_config(_load_config_data(path), str(path))
    message = str(exc_info.value)
    assert f"The '{key}' key is no longer used." in message
    assert REPLACED_CONFIG_KEYS[key] in message


def test_config_replaced_key_other_section():
    """A nested key is only recognized in its own section, which may be of the wrong type.

    Such mistakes are left to the validation of the config file.
    """
    _check_outdated_config({"description": "x", "metadata": "x", "access": None}, "c.yaml")


CONFIG_YAML_SCALARS = """\
path_record_id: .zenodo-record-id.txt
metadata:
  title: 'A title'
  version: '1.0.0'
  license: cc-by-4.0
  resource_type: dataset
  publisher: Zenodo
  creators:
    - family_name: Verstraelen
      given_name: Toon
  keywords: coffee
custom_fields:
  programming_languages: python
"""

CONFIG_YAML_LISTS = """\
path_record_id: .zenodo-record-id.txt
metadata:
  title: 'A title'
  version: '1.0.0'
  license:
    - cc-by-4.0
  resource_type: dataset
  publisher: Zenodo
  creators:
    - family_name: Verstraelen
      given_name: Toon
  keywords:
    - coffee
custom_fields:
  programming_languages:
    - python
"""


def test_config_scalar_where_a_list_belongs(tmp_path):
    """A single value is read as a one element list, everywhere a list of strings belongs."""
    config = _write_config(tmp_path, "scalars.yaml", CONFIG_YAML_SCALARS)
    assert config.metadata.license == ["cc-by-4.0"]
    assert config.metadata.keywords == ["coffee"]
    assert config.custom_fields.programming_languages == ["python"]
    listed = _write_config(tmp_path, "lists.yaml", CONFIG_YAML_LISTS)
    assert config.to_zenodo(DESCRIPTION, []) == listed.to_zenodo(DESCRIPTION, [])


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            CONFIG_YAML_SCALARS.replace(
                "programming_languages: python", "programming_languages: 3"
            ),
            "Expected a string or a list of strings, got int",
        ),
        (
            CONFIG_YAML_SCALARS.replace("keywords: coffee", "keywords: null"),
            "Expected a string or a list of strings, got NoneType",
        ),
        (
            CONFIG_YAML_SCALARS.replace("keywords: coffee", "keywords: [coffee, 3]"),
            "Expected a string, got int",
        ),
    ],
)
def test_config_scalar_where_a_list_belongs_invalid(tmp_path, text, expected):
    with pytest.raises(ClassValidationError) as exc_info:
        _write_config(tmp_path, "sync_zenodo.yaml", text)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any(expected in message for message in messages)


@pytest.fixture(autouse=True)
def online(monkeypatch):
    """Run every test as in a build that is not offline, also when pytest runs in a StepUp step."""
    monkeypatch.delenv("STEPUP_BUILD_OFFLINE", raising=False)


@pytest.fixture(autouse=True)
def amended(monkeypatch) -> list[list[Path]]:
    """Record the inputs amended by `srr-sync-zenodo` instead of sending them to StepUp.

    Outside a StepUp step, `amend()` prints the call to the standard output,
    which would get mixed with the output of `--dry-run`.

    Returns
    -------
    amended
        The input paths of every call of `amend()`, in the order of the calls.
    """
    calls = []

    def amend(inp=()):
        calls.append(list(inp))

    monkeypatch.setattr("stepup.reprep.sync_zenodo.amend", amend)
    return calls


def _write_inventory(tmp_path, files: list[UploadFile] | None = None) -> str:
    """Write an inventory in `tmp_path` and return its path.

    Without `files`, the inventory lists one file, because an empty inventory is refused.
    """
    path = Path(tmp_path) / "zenodo_inventory.jsonl"
    if files is None:
        files = [_local_file(tmp_path, "one.txt", "hello")]
    _write_inventory_file(path, files)
    return str(path)


def _write_inventory_file(path_inventory: str, files: list[UploadFile]):
    """Write an inventory with the given MD5 checksums, which need not match the files."""
    root = Path(path_inventory).parent
    header = InventoryHeader("md5")
    with open(path_inventory, "w", encoding="utf-8", newline="\n") as fh:
        print(format_header(header), file=fh)
        for file in files:
            size = file.path.size if file.path.is_file() else 0
            record = FileRecord(str(file.path.relpath(root).normpath()), file.md5, size)
            print(format_record(record, header), file=fh)


def _write_description(tmp_path) -> str:
    """Write a description in Markdown in `tmp_path` and return its path."""
    path = tmp_path / "zenodo_description.md"
    path.write_text("A *dataset*.\n", encoding="utf-8", newline="\n")
    return str(path)


def test_main_dry_run(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("REPREP_ZENODO_TOKEN", raising=False)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML, encoding="utf-8", newline="\n")
    args = [str(path), _write_description(tmp_path), _write_inventory(tmp_path)]
    assert main([*args, "--dry-run"]) == 0
    out = capsys.readouterr().out
    # Pop the first line, which is just a message explaining the output below.
    out = out[out.find("{") :]
    payload = json.loads(out)
    assert payload["metadata"]["title"] == "A title"
    assert payload["metadata"]["description"] == "<p>A <em>dataset</em>.</p>\n"
    assert payload["files"] == {"enabled": True, "default_preview": "one.txt"}
    assert "endpoint" not in payload


@pytest.mark.parametrize("args", [[], ["--dry-run"]])
def test_main_empty_inventory(tmp_path, monkeypatch, capsys, args):
    """An empty inventory is refused before any request is sent, also with `--dry-run`."""
    monkeypatch.setenv("REPREP_ZENODO_TOKEN", "token")
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML, encoding="utf-8", newline="\n")

    def fail(*args, **kwargs):
        raise AssertionError("No request may be sent.")

    monkeypatch.setattr(ZenodoWrapper, "__init__", fail)
    inventory = _write_inventory(tmp_path, [])
    assert main([str(path), _write_description(tmp_path), inventory, *args]) == 1
    captured = capsys.readouterr()
    assert "lists no files" in captured.err
    assert "metadata only" in captured.err
    assert "Traceback" not in captured.err


def test_main_dry_run_files(tmp_path, monkeypatch, capsys):
    """The first file of the inventory is the preview, also when another one sorts first."""
    monkeypatch.delenv("REPREP_ZENODO_TOKEN", raising=False)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML, encoding="utf-8", newline="\n")
    (tmp_path / "sub").mkdir()
    files = [_local_file(tmp_path, "sub/two.txt", "bye"), _local_file(tmp_path, "one.txt", "hi")]
    args = [str(path), _write_description(tmp_path), _write_inventory(tmp_path, files)]
    assert main([*args, "--dry-run"]) == 0
    out = capsys.readouterr().out
    payload = json.loads(out[out.find("{") :])
    assert payload["files"] == {
        "enabled": True,
        "default_preview": "two.txt",
    }


def test_main_invalid_config(tmp_path, monkeypatch, capsys):
    """A config file that Zenodo would reject is reported without a traceback.

    Every problem is listed, because `cattrs` collects them all before it gives up.
    """
    monkeypatch.delenv("REPREP_ZENODO_TOKEN", raising=False)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(
        CONFIG_YAML.replace("version: '1.0.0'", "version: 1.0").replace(
            "  publisher: Zenodo\n", ""
        ),
        encoding="utf-8",
        newline="\n",
    )
    args = [str(path), _write_description(tmp_path), _write_inventory(tmp_path)]
    assert main([*args, "--dry-run"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    # The message is reproduced verbatim, so `rich` does not wrap it at eighty columns.
    assert "Expected a string, got float: 1.0. Enclose the value in quotes" in captured.err
    assert "metadata.publisher" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("missing.md", "Description file missing.md does not exist"),
        ("notes.txt", "must be a Markdown (.md) or HTML (.html) file"),
    ],
)
def test_main_user_error(tmp_path, monkeypatch, capsys, description, expected):
    """Everything the user can get wrong is reported as a message, not as a traceback."""
    monkeypatch.delenv("REPREP_ZENODO_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML, encoding="utf-8", newline="\n")
    assert main([str(path), description, _write_inventory(tmp_path), "--dry-run"]) == 1
    captured = capsys.readouterr()
    assert expected in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(("name", "content"), [("d.md", ""), ("d.md", "\n\n"), ("d.html", "x")])
def test_main_short_description(tmp_path, monkeypatch, capsys, name, content):
    """A description that Zenodo would refuse is reported as a message, not as a traceback."""
    monkeypatch.delenv("REPREP_ZENODO_TOKEN", raising=False)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML, encoding="utf-8", newline="\n")
    path_description = tmp_path / name
    path_description.write_text(content, encoding="utf-8", newline="\n")
    args = [str(path), str(path_description), _write_inventory(tmp_path)]
    assert main([*args, "--dry-run"]) == 1
    captured = capsys.readouterr()
    assert "holds too little text" in captured.err
    assert "Traceback" not in captured.err


def test_main_rest_error(tmp_path, monkeypatch, capsys):
    """A request that Zenodo refuses is reported with the message of the response."""
    monkeypatch.setenv("REPREP_ZENODO_TOKEN", "token")
    # The record id file of the config is a relative path, so it must not land in the repository.
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML, encoding="utf-8", newline="\n")

    def fail(*args, **kwargs):
        raise RESTError("Failed POST https://zenodo.org/api/records: 400")

    monkeypatch.setattr(ZenodoWrapper, "create_new_record", fail)
    assert main([str(path), _write_description(tmp_path), _write_inventory(tmp_path)]) == 1
    assert "Failed POST" in capsys.readouterr().err


def test_metadata_creators_required():
    """Zenodo rejects a record without creators, so it is rejected locally."""
    with pytest.raises(ValueError):
        Metadata(
            title="A title",
            version="1.0.0",
            license=["mit"],
            resource_type="dataset",
            creators=[],
            publisher="Zenodo",
        )


def test_metadata_publisher_required():
    """Zenodo refuses to publish a record without a publisher, so it is required locally."""
    with pytest.raises(TypeError):
        Metadata(
            title="A title",
            version="1.0.0",
            license=["mit"],
            resource_type="dataset",
            creators=[Creator("Verstraelen", "Toon")],
        )


def test_metadata_publisher_empty():
    with pytest.raises(ValueError):
        _metadata(license=["mit"], resource_type="dataset", publisher="")


def test_metadata_publisher_in_payload():
    metadata = _metadata(license=["mit"], resource_type="dataset", publisher="Ghent University")
    assert metadata.to_zenodo(DESCRIPTION)["publisher"] == "Ghent University"


def test_config_publisher_missing(tmp_path):
    """A config file without a publisher is rejected with a message naming the key."""
    text = CONFIG_YAML.replace("  publisher: Zenodo\n", "")
    with pytest.raises(ClassValidationError) as exc_info:
        _write_config(tmp_path, "sync_zenodo.yaml", text)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any("publisher" in message for message in messages)


@pytest.mark.parametrize("title", ["", "ab"])
def test_metadata_title_too_short(title):
    """Zenodo reads a title of at least three characters."""
    with pytest.raises(ValueError):
        _metadata(title=title, license=["mit"], resource_type="dataset")


@pytest.mark.parametrize(
    ("field", "value"),
    [("version", "1" * 192), ("version", ""), ("copyright", "")],
)
def test_metadata_length_bounds(field, value):
    """The length bounds Zenodo enforces are checked locally."""
    with pytest.raises(ValueError):
        _metadata(license=["mit"], resource_type="dataset", **{field: value})


@pytest.mark.parametrize("version", ["1.0.0", "v1.0.0", "2024-06-01", "latest", "0.1.0-rc.1"])
def test_metadata_version_any_convention(version):
    """Any non-empty version string is accepted, whatever the convention."""
    assert _metadata(version=version, license=["mit"], resource_type="dataset").version == version


def test_creator_family_name_required():
    """Zenodo requires a family name for a personal creator."""
    with pytest.raises(TypeError):
        Creator()
    with pytest.raises(ValueError):
        Creator("")


def test_config_creators_missing(tmp_path):
    """A config file without creators is rejected with a message naming the key."""
    text = CONFIG_YAML[: CONFIG_YAML.index("  creators:")]
    with pytest.raises(ClassValidationError) as exc_info:
        _write_config(tmp_path, "sync_zenodo.yaml", text)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any("creators" in message for message in messages)


def _v1_record(rid: int, checksums: dict[str, str | None], **kwargs) -> dict:
    """Build a record as Zenodo serializes it for `application/vnd.inveniordm.v1+json`.

    A `None` checksum builds the entry of a file
    that is declared with `start_uploads` and whose content is not uploaded yet.
    """
    return {
        "id": rid,
        "links": {"self_html": f"https://zenodo.org/record/{rid}"},
        "files": {
            "enabled": len(checksums) > 0,
            "order": [],
            "count": len(checksums),
            "total_bytes": 0,
            "entries": {
                name: {"key": name}
                if md5 is None
                else {"key": name, "checksum": f"md5:{md5}", "size": 0}
                for name, md5 in checksums.items()
            },
        },
        **kwargs,
    }


def _local_file(tmp_path, name: str, content: str) -> UploadFile:
    """Write a local file and return its entry in an up-to-date inventory."""
    path = Path(tmp_path) / name
    path.write_text(content, encoding="utf-8")
    return UploadFile(path, _md5(content))


def _md5(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


class _FakeZenodo:
    """A `ZenodoWrapper` stub that records the calls made on it."""

    def __init__(self, record=None, versions=None, metadata_errors=()):
        self.record = record
        self.versions = [record] if versions is None else versions
        self.metadata_errors = list(metadata_errors)
        """The soft errors in the response to every metadata update."""
        self.calls = []
        self.files_options = []
        """The files options of every metadata update, as they are sent to Zenodo."""

    def create_new_record(self, config, description):
        self.calls.append(("create_new_record",))
        if self.record is None:
            self.record = _v1_record(7, {})
        return self.record

    def get_record(self, rid):
        self.calls.append(("get_record", rid))
        return self.record

    def get_versions(self, rid):
        self.calls.append(("get_versions", rid))
        return self.versions

    def delete_file(self, rid, name):
        self.calls.append(("delete_file", name))

    def start_uploads(self, rid, files):
        self.calls.append(("start_uploads", [file.name for file in files]))

    def upload_file(self, rid, file):
        self.calls.append(("upload_file", file.name))

    def update_metadata(self, rid, config, description, files, publication_date=None):
        self.calls.append(("update_metadata", rid, publication_date))
        data = config.to_zenodo(description, files, publication_date)
        self.files_options.append(data["files"])
        if len(self.metadata_errors) > 0:
            return self.record | {"errors": self.metadata_errors}
        return self.record

    def edit_record(self, rid):
        self.calls.append(("edit_record", rid))

    def publish_record(self, rid):
        self.calls.append(("publish_record", rid))

    def create_new_version(self, rid):
        self.calls.append(("create_new_version", rid))
        return self.record


def test_search_hits():
    assert _search_hits({"hits": {"hits": [{"id": 1}], "total": 1}}) == [{"id": 1}]


@pytest.mark.parametrize("data", [{}, {"hits": []}, {"hits": {"hits": {}}}])
def test_search_hits_unexpected_shape(data):
    """The legacy representation, which does not paginate, is reported as such."""
    with pytest.raises(ZenodoError) as exc_info:
        _search_hits(data)
    assert INVENIORDM_MIMETYPE in str(exc_info.value)


class _FakeResponse:
    """A `requests` response with a given status code and body."""

    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = text

    def json(self):
        return json.loads(self.text)


@pytest.mark.parametrize("body", ["<html>Bad Gateway</html>", '{"message": "Bad Gateway"}', ""])
def test_rest_request_error(monkeypatch, body):
    """An error is reported with its body, which Zenodo does not always describe in JSON.

    A gateway between the client and Zenodo may answer with an HTML page instead.
    """
    monkeypatch.setattr(requests, "request", lambda *args, **kwargs: _FakeResponse(502, body))
    with pytest.raises(RESTError) as exc_info:
        RESTWrapper("https://zenodo.org/api", {}).get("records/7")
    message = str(exc_info.value)
    assert "GET https://zenodo.org/api/records/7: 502" in message
    assert body in message
    assert exc_info.value.status_code == 502


def test_rest_request_json_response(monkeypatch):
    monkeypatch.setattr(
        requests, "request", lambda *args, **kwargs: _FakeResponse(200, '{"id": 7}')
    )
    assert RESTWrapper("https://zenodo.org/api", {}).get("records/7") == {"id": 7}


def test_rest_request_empty_response(monkeypatch):
    """A request that Zenodo answers without a body, such as a delete, returns nothing."""
    monkeypatch.setattr(requests, "request", lambda *args, **kwargs: _FakeResponse(204, ""))
    assert RESTWrapper("https://zenodo.org/api", {}).delete("records/7/draft") is None


def test_rest_request_timeout_default(monkeypatch):
    """Every request is bounded in time, so a stalled connection cannot hang a build."""
    seen = {}

    def request(method, url, **kwargs):
        seen.update(kwargs)
        return _FakeResponse(200, "{}")

    monkeypatch.setattr(requests, "request", request)
    RESTWrapper("https://zenodo.org/api", {}).get("records/7")
    assert seen["timeout"] == REQUEST_TIMEOUT
    RESTWrapper("https://zenodo.org/api", {}).get("records/7", timeout=1.0)
    assert seen["timeout"] == 1.0


def test_rest_request_unreachable(monkeypatch):
    """A request that never reaches Zenodo is reported like a refused one."""

    def request(*args, **kwargs):
        raise requests.ConnectionError("Name or service not known")

    monkeypatch.setattr(requests, "request", request)
    with pytest.raises(RESTError) as exc_info:
        RESTWrapper("https://zenodo.org/api", {}).get("records/7")
    assert "Name or service not known" in str(exc_info.value)
    assert exc_info.value.status_code is None


@pytest.mark.parametrize("name", ["fig#1.png", "a b.txt", "100%.csv", "a?b.txt", "a/b.txt"])
def test_file_loc_escapes_name(name):
    """A file name becomes a single path segment, whatever characters it holds."""
    loc = _file_loc("7", name)
    assert loc.startswith("records/7/draft/files/")
    segment = loc[len("records/7/draft/files/") :]
    assert unquote(segment) == name
    assert not any(char in segment for char in "#?/")


class _FakeRest:
    """A `RESTWrapper` stub that serves a paginated search result."""

    def __init__(self, hits):
        self.hits = hits
        self.calls = []
        self.posted = []

    def get(self, loc, params):
        self.calls.append((loc, params["page"]))
        page, size = params["page"], params["size"]
        return {
            "hits": {"hits": self.hits[(page - 1) * size : page * size], "total": len(self.hits)}
        }

    def post(self, loc, json):
        self.posted.append((loc, json))


@pytest.mark.parametrize("num", [0, 1, SEARCH_PAGE_SIZE, SEARCH_PAGE_SIZE + 1])
def test_get_versions_pagination(num):
    """The version chain is collected from all pages of the search result."""
    hits = [{"id": rid} for rid in range(num)]
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest(hits)
    assert zenodo.get_versions("3") == hits
    num_pages = num // SEARCH_PAGE_SIZE + 1
    assert zenodo.rest.calls == [("records/3/versions", page) for page in range(1, num_pages + 1)]


def test_record_files_entries():
    """The file entries are read from the InvenioRDM representation."""
    record = _v1_record(1, {"one.txt": "abc"})
    assert _get_record_files(record) == {
        "one.txt": {"key": "one.txt", "checksum": "md5:abc", "size": 0}
    }


def test_record_files_without_files():
    """A record whose files are disabled has no entries."""
    assert _get_record_files({"id": 1, "files": {"enabled": False}}) == {}


def test_record_files_unexpected_shape():
    """The legacy representation, which lists the files, is reported as such."""
    with pytest.raises(ZenodoError) as exc_info:
        _get_record_files({"id": 1, "files": [{"key": "one.txt", "checksum": "md5:abc"}]})
    assert INVENIORDM_MIMETYPE in str(exc_info.value)


def test_entry_md5():
    assert _entry_md5({"checksum": f"md5:{_md5('hello')}"}) == _md5("hello")


@pytest.mark.parametrize("checksum", ["sha256:abc", "abc", ""])
def test_entry_md5_unexpected_format(checksum):
    """A digest of another algorithm cannot be compared to a local MD5 sum."""
    with pytest.raises(ZenodoError) as exc_info:
        _entry_md5({"checksum": checksum})
    assert "unexpected checksum format" in str(exc_info.value)


def test_refresh_files_unchanged(tmp_path):
    file = _local_file(tmp_path, "one.txt", "hello")
    record = _v1_record(1, {"one.txt": _md5("hello")})
    zenodo = _FakeZenodo()
    _refresh_files(zenodo, "1", record, {"one.txt": file}, "1.0.0")
    assert zenodo.calls == []


def test_refresh_files_upload_new(tmp_path):
    file = _local_file(tmp_path, "one.txt", "hello")
    record = _v1_record(1, {})
    zenodo = _FakeZenodo()
    _refresh_files(zenodo, "1", record, {"one.txt": file}, "1.0.0")
    assert zenodo.calls == [("start_uploads", ["one.txt"]), ("upload_file", "one.txt")]


def test_refresh_files_declare_together(tmp_path):
    """A replaced and a new file are declared in one request, after the deletion."""
    file_one = _local_file(tmp_path, "one.txt", "hello")
    file_two = _local_file(tmp_path, "two.txt", "bye")
    record = _v1_record(1, {"one.txt": _md5("old")})
    zenodo = _FakeZenodo()
    _refresh_files(zenodo, "1", record, {"one.txt": file_one, "two.txt": file_two}, "1.0.0")
    assert zenodo.calls == [
        ("delete_file", "one.txt"),
        ("start_uploads", ["one.txt", "two.txt"]),
        ("upload_file", "one.txt"),
        ("upload_file", "two.txt"),
    ]


def test_refresh_files_replace_changed(tmp_path):
    file = _local_file(tmp_path, "one.txt", "hello")
    record = _v1_record(1, {"one.txt": _md5("bye")})
    zenodo = _FakeZenodo()
    _refresh_files(zenodo, "1", record, {"one.txt": file}, "1.0.0")
    assert zenodo.calls == [
        ("delete_file", "one.txt"),
        ("start_uploads", ["one.txt"]),
        ("upload_file", "one.txt"),
    ]


def test_refresh_files_complete_pending(tmp_path):
    """A file that was declared but never uploaded is completed, not compared to a checksum."""
    file = _local_file(tmp_path, "one.txt", "hello")
    record = _v1_record(1, {"one.txt": None})
    zenodo = _FakeZenodo()
    _refresh_files(zenodo, "1", record, {"one.txt": file}, "1.0.0")
    # The file is declared already, so it is neither deleted nor declared again.
    assert zenodo.calls == [("upload_file", "one.txt")]


def test_refresh_files_pending_next_to_uploaded(tmp_path):
    """Only the pending file of a half finished upload is sent again."""
    file_one = _local_file(tmp_path, "one.txt", "hello")
    file_two = _local_file(tmp_path, "two.txt", "bye")
    record = _v1_record(1, {"one.txt": _md5("hello"), "two.txt": None})
    zenodo = _FakeZenodo()
    files = {"one.txt": file_one, "two.txt": file_two}
    _refresh_files(zenodo, "1", record, files, "1.0.0")
    assert zenodo.calls == [("upload_file", "two.txt")]


def test_refresh_files_delete_pending_removed(tmp_path):
    """A pending file that is no longer listed locally is removed like an uploaded one."""
    record = _v1_record(1, {"gone.txt": None})
    zenodo = _FakeZenodo()
    _refresh_files(zenodo, "1", record, {}, "1.0.0")
    assert zenodo.calls == [("delete_file", "gone.txt")]


def test_refresh_draft_completes_failed_upload(tmp_path):
    """The run after a failed upload completes the draft, as `_upload_new_record` promises.

    The first run declares both files and fails while sending the content of the first one.
    The second run finds one pending entry and no uploaded entry, and sends both.
    """
    file_one = _local_file(tmp_path, "one.txt", "hello")
    file_two = _local_file(tmp_path, "two.txt", "bye")
    config = _config_with_version(tmp_path, "1.0.0")
    zenodo = _FakeZenodo(_v1_record(7, {}))

    def fail(rid, file):
        raise RESTError("Failed PUT https://zenodo.org/api/records/7/draft/files: 500")

    zenodo.upload_file = fail
    with pytest.raises(RESTError):
        _upload_new_record(zenodo, config, DESCRIPTION, [file_one, file_two])
    assert config.path_record_id.read_text(encoding="utf-8").strip() == "7"

    # Zenodo now holds the names of both files without their content.
    draft = _v1_record(7, {"one.txt": None, "two.txt": None}, is_published=False)
    zenodo = _FakeZenodo(draft)
    _refresh_draft(zenodo, "7", draft, config, DESCRIPTION, [file_one, file_two])
    assert zenodo.calls == [
        ("upload_file", "one.txt"),
        ("upload_file", "two.txt"),
        ("update_metadata", "7", None),
    ]


def test_refresh_draft_replace_preview(tmp_path):
    """A draft whose preview file is replaced by a new one selects it after the upload."""
    file = _local_file(tmp_path, "new.txt", "hello")
    config = _config_with_version(tmp_path, "1.0.0")
    draft = _v1_record(7, {"old.txt": _md5("bye")}, is_published=False)
    zenodo = _FakeZenodo(draft)
    _refresh_draft(zenodo, "7", draft, config, DESCRIPTION, [file])
    assert zenodo.calls == [
        ("delete_file", "old.txt"),
        ("start_uploads", ["new.txt"]),
        ("upload_file", "new.txt"),
        ("update_metadata", "7", None),
    ]
    assert zenodo.files_options == [{"enabled": True, "default_preview": "new.txt"}]


def test_refresh_draft_delete_preview(tmp_path):
    """Deleting the preview file of a draft selects the file that is now first.

    Zenodo clears the preview of a deleted file itself,
    so the preview needs no update before the file is deleted.
    """
    file_two = _local_file(tmp_path, "two.txt", "bye")
    config = _config_with_version(tmp_path, "1.0.0")
    draft = _v1_record(7, {"one.txt": _md5("hello"), "two.txt": _md5("bye")}, is_published=False)
    draft["files"]["default_preview"] = "one.txt"
    zenodo = _FakeZenodo(draft)
    _refresh_draft(zenodo, "7", draft, config, DESCRIPTION, [file_two])
    assert zenodo.calls == [("delete_file", "one.txt"), ("update_metadata", "7", None)]
    assert zenodo.files_options == [{"enabled": True, "default_preview": "two.txt"}]


def test_refresh_files_delete_removed(tmp_path):
    record = _v1_record(1, {"gone.txt": _md5("hello")})
    zenodo = _FakeZenodo()
    _refresh_files(zenodo, "1", record, {}, "1.0.0")
    assert zenodo.calls == [("delete_file", "gone.txt")]


def test_diff_files_classifies_every_name(tmp_path):
    files = {
        name: _local_file(tmp_path, name, text)
        for name, text in [("same", "a"), ("changed", "b"), ("pending", "c"), ("missing", "d")]
    }
    record = _v1_record(
        1,
        {
            "extra": _md5("e"),
            "same": _md5("a"),
            "changed": _md5("old"),
            "pending": None,
        },
    )
    assert _diff_files(record, files) == FileDiff(
        missing=["missing"],
        extra=["extra"],
        changed=["changed"],
        same=["same"],
        incomplete=["pending"],
    )


def test_diff_files_empty():
    assert _diff_files(_v1_record(1, {}), {}) == FileDiff([], [], [], [], [])


def test_diff_files_has_no_side_effects(tmp_path):
    files = {"one.txt": _local_file(tmp_path, "one.txt", "hello")}
    record = _v1_record(1, {"one.txt": _md5("bye")})
    _diff_files(record, files)
    assert record == _v1_record(1, {"one.txt": _md5("bye")})


def test_diff_files_unexpected_checksum(tmp_path):
    files = {"one.txt": _local_file(tmp_path, "one.txt", "hello")}
    record = _v1_record(1, {"one.txt": None})
    record["files"]["entries"]["one.txt"]["checksum"] = "sha256:abc"
    with pytest.raises(ZenodoError):
        _diff_files(record, files)


def test_check_record_md5_ok(tmp_path):
    file = _local_file(tmp_path, "one.txt", "hello")
    _check_record_md5(_v1_record(1, {"one.txt": _md5("hello")}), {"one.txt": file}, "1.0.0")


def test_check_record_md5_mismatch(tmp_path):
    file = _local_file(tmp_path, "one.txt", "hello")
    with pytest.raises(ZenodoError):
        _check_record_md5(_v1_record(1, {"one.txt": _md5("bye")}), {"one.txt": file}, "1.0.0")


def test_check_record_md5_missing_locally(tmp_path):
    with pytest.raises(ZenodoError):
        _check_record_md5(_v1_record(1, {"gone.txt": _md5("hello")}), {}, "1.0.0")


def test_check_record_md5_missing_online(tmp_path):
    file = _local_file(tmp_path, "one.txt", "hello")
    with pytest.raises(ZenodoError):
        _check_record_md5(_v1_record(1, {}), {"one.txt": file}, "1.0.0")


def test_check_record_md5_incomplete(tmp_path):
    file = _local_file(tmp_path, "one.txt", "hello")
    with pytest.raises(ZenodoError) as exc_info:
        _check_record_md5(_v1_record(1, {"one.txt": None}), {"one.txt": file}, "1.0.0")
    assert "no checksum" in str(exc_info.value)


def _config_with_version(tmp_path, version: str) -> Config:
    """Load `CONFIG_YAML` with a given version and a record ID file inside `tmp_path`."""
    text = CONFIG_YAML.replace("version: '1.0.0'", f"version: '{version}'").replace(
        "path_record_id: .zenodo-record-id.txt",
        f"path_record_id: {tmp_path / '.zenodo-record-id.txt'}",
    )
    return _write_config(tmp_path, "sync_zenodo.yaml", text)


PUBLICATION_DATE = "2024-06-01"
"""The publication date of a record that was published before the tests run."""


def _published(rid, version: str, checksums: dict[str, str] | None = None, is_latest=True) -> dict:
    """Build a published record with its place in the version chain."""
    return _v1_record(
        rid,
        {} if checksums is None else checksums,
        is_published=True,
        metadata={"version": version, "publication_date": PUBLICATION_DATE},
        versions={"is_latest": is_latest},
    )


def test_refresh_existing_record_published_same_version(tmp_path):
    """A published record is recognized through `is_published` and republished."""
    config = _config_with_version(tmp_path, "1.0.0")
    zenodo = _FakeZenodo(_published(7, "1.0.0"))
    _refresh_existing_record(zenodo, "7", config, DESCRIPTION, [])
    assert zenodo.calls == [
        ("get_record", "7"),
        ("get_versions", "7"),
        ("edit_record", "7"),
        ("update_metadata", "7", PUBLICATION_DATE),
        ("publish_record", "7"),
    ]


@pytest.mark.parametrize("version", ["1.1.0", "0.9.0", "2024-06-01", "second-release"])
def test_refresh_existing_record_published_unpublished_version(tmp_path, version):
    """Any local version that was never published becomes a new version on Zenodo."""
    config = _config_with_version(tmp_path, version)
    zenodo = _FakeZenodo(_published(7, "1.0.0"))
    _refresh_existing_record(zenodo, "7", config, DESCRIPTION, [])
    assert ("create_new_version", "7") in zenodo.calls
    # A new version is published on the day it is created, not on the day the parent was.
    assert ("update_metadata", "7", None) in zenodo.calls
    assert config.path_record_id.read_text(encoding="utf-8").strip() == "7"


def test_refresh_existing_record_published_version_taken(tmp_path):
    """A local version that is already published as an older version is refused."""
    config = _config_with_version(tmp_path, "1.0.0")
    versions = [_published(7, "1.0.0", is_latest=False), _published(8, "1.1.0")]
    zenodo = _FakeZenodo(versions[1], versions)
    with pytest.raises(ZenodoError) as exc_info:
        _refresh_existing_record(zenodo, "8", config, DESCRIPTION, [])
    assert "already published as record 7" in str(exc_info.value)


def test_refresh_existing_record_published_stale_record_id(tmp_path):
    """A record id pointing to an older version is refused, even at a matching version."""
    config = _config_with_version(tmp_path, "1.0.0")
    versions = [_published(7, "1.0.0", is_latest=False), _published(8, "1.1.0")]
    zenodo = _FakeZenodo(versions[0], versions)
    with pytest.raises(ZenodoError) as exc_info:
        _refresh_existing_record(zenodo, "7", config, DESCRIPTION, [])
    assert "not the latest published version" in str(exc_info.value)
    assert str(config.path_record_id) in str(exc_info.value)


def test_check_version_chain_without_latest(tmp_path):
    """A version chain in which Zenodo marks no latest version is reported as such."""
    config = _config_with_version(tmp_path, "1.0.0")
    record = _published(7, "1.0.0", is_latest=False)
    with pytest.raises(ZenodoError) as exc_info:
        _check_version_chain(_FakeZenodo(record), record, config)
    assert INVENIORDM_MIMETYPE in str(exc_info.value)


def test_check_version_chain_mixed_id_types(tmp_path):
    """Record ids are compared as strings, because Zenodo may serialize them either way."""
    config = _config_with_version(tmp_path, "1.1.0")
    record = _published(7, "1.0.0")
    _check_version_chain(_FakeZenodo(record, [_published("7", "1.0.0")]), record, config)


def test_refresh_existing_record_draft(tmp_path):
    """A draft is recognized through `is_published` and its metadata is updated in place."""
    file = _local_file(tmp_path, "one.txt", "hello")
    config = _config_with_version(tmp_path, "1.0.0")
    record = _v1_record(7, {}, is_published=False, metadata={"version": "1.0.0"})
    zenodo = _FakeZenodo(record)
    _refresh_existing_record(zenodo, "7", config, DESCRIPTION, [file])
    assert zenodo.calls == [
        ("get_record", "7"),
        ("start_uploads", ["one.txt"]),
        ("upload_file", "one.txt"),
        ("update_metadata", "7", None),
    ]


SOFT_ERRORS = [
    {"field": "metadata.title", "messages": ["Shorter than minimum length 3."]},
    {
        "field": "metadata.publisher",
        "messages": ["Missing publisher field required for DOI registration."],
    },
]
"""Soft errors as Zenodo lists them in a successful response to a metadata update."""


def _main_with_fake_zenodo(tmp_path, monkeypatch, zenodo: _FakeZenodo) -> int:
    """Run `main` with `CONFIG_YAML` in `tmp_path`, sending the requests to `zenodo`."""
    monkeypatch.setenv("REPREP_ZENODO_TOKEN", "token")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("stepup.reprep.sync_zenodo.ZenodoWrapper", lambda *a, **kw: zenodo)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML, encoding="utf-8", newline="\n")
    return main([str(path), _write_description(tmp_path), _write_inventory(tmp_path)])


def _assert_soft_errors_reported(stderr: str, rid: str):
    for error in SOFT_ERRORS:
        assert f"{error['field']}: {error['messages'][0]}" in stderr
    assert f"record {rid}" in stderr
    assert "draft is kept" in stderr
    assert "Traceback" not in stderr


def test_main_soft_errors_new_draft(tmp_path, monkeypatch, capsys):
    """Soft errors in the metadata update of a new draft fail the run.

    The missing files reported on creation are expected, so they are not reported,
    and the record id is kept, so the next run repairs the draft.
    """
    record = _v1_record(7, {}, is_published=False)
    record["errors"] = [{"field": "files.enabled", "messages": ["Missing uploaded files."]}]
    zenodo = _FakeZenodo(record, metadata_errors=SOFT_ERRORS)
    assert _main_with_fake_zenodo(tmp_path, monkeypatch, zenodo) == 1
    assert ("update_metadata", "7", None) in zenodo.calls
    assert not any(call[0] == "publish_record" for call in zenodo.calls)
    stderr = capsys.readouterr().err
    _assert_soft_errors_reported(stderr, "7")
    assert "Missing uploaded files" not in stderr
    assert (tmp_path / ".zenodo-record-id.txt").read_text(encoding="utf-8") == "7\n"


def test_main_soft_errors_republish(tmp_path, monkeypatch, capsys):
    """Soft errors in the metadata update of a published record prevent its publication."""
    (tmp_path / ".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    record = _published(7, "1.0.0", {"one.txt": _md5("hello")})
    zenodo = _FakeZenodo(record, metadata_errors=SOFT_ERRORS)
    assert _main_with_fake_zenodo(tmp_path, monkeypatch, zenodo) == 1
    assert ("update_metadata", "7", PUBLICATION_DATE) in zenodo.calls
    assert not any(call[0] == "publish_record" for call in zenodo.calls)
    _assert_soft_errors_reported(capsys.readouterr().err, "7")


@pytest.mark.parametrize("errors", [None, []])
def test_check_draft_errors_none(errors):
    _check_draft_errors({"id": 7, "errors": errors}, "7")
    _check_draft_errors({"id": 7}, "7")


def test_check_draft_errors_unexpected_shape():
    """An error that Zenodo formats differently is still reported, as it arrived."""
    with pytest.raises(ZenodoError) as exc_info:
        _check_draft_errors({"errors": ["something odd"]}, "7")
    assert "'something odd'" in str(exc_info.value)


@pytest.mark.parametrize("record_is_published", [True, False])
def test_is_published(record_is_published):
    assert _is_published({"id": 7, "is_published": record_is_published}) is record_is_published


@pytest.mark.parametrize("record", [{"id": 7}, {"id": 7, "is_published": None}])
def test_is_published_unexpected_shape(record):
    """A record that does not say whether it is published is reported as such.

    Guessing would send the requests meant for a draft to a published record, or vice versa.
    """
    with pytest.raises(ZenodoError) as exc_info:
        _is_published(record)
    assert INVENIORDM_MIMETYPE in str(exc_info.value)


def test_refresh_existing_record_without_is_published(tmp_path):
    """The status of a record is never guessed, not even to refresh an existing one."""
    config = _config_with_version(tmp_path, "1.0.0")
    record = _v1_record(7, {}, metadata={"version": "1.0.0"})
    with pytest.raises(ZenodoError) as exc_info:
        _refresh_existing_record(_FakeZenodo(record), "7", config, DESCRIPTION, [])
    assert INVENIORDM_MIMETYPE in str(exc_info.value)


def test_record_version_present():
    assert _get_record_version(_published(7, "1.0.0")) == "1.0.0"


@pytest.mark.parametrize("record", [{"id": 7}, {"id": 7, "metadata": {}}])
def test_record_version_absent(record):
    """Zenodo does not require a version, so a record may carry none."""
    assert _get_record_version(record) is None


def test_record_publication_date_present():
    assert _record_publication_date(_published(7, "1.0.0")) == PUBLICATION_DATE


@pytest.mark.parametrize("record", [{"id": 7}, {"id": 7, "metadata": {}}])
def test_record_publication_date_absent(record):
    assert _record_publication_date(record) is None


def test_metadata_omits_unset_fields():
    """A field without a value is left out, instead of being sent as a null or an empty list."""
    payload = _metadata(resource_type="dataset").to_zenodo(DESCRIPTION)
    assert sorted(payload) == [
        "creators",
        "description",
        "publication_date",
        "publisher",
        "resource_type",
        "title",
        "version",
    ]


def test_metadata_keywords_are_subjects():
    """Zenodo has no keyword field, so the keywords are deposited as free text subjects."""
    metadata = _metadata(resource_type="dataset", keywords=["coffee", "tea"])
    payload = metadata.to_zenodo(DESCRIPTION)
    assert payload["subjects"] == [{"subject": "coffee"}, {"subject": "tea"}]
    assert "keywords" not in payload


def test_creator_omits_unset_fields():
    """A creator known by family name only is not sent with a null given name."""
    payload = Creator("Verstraelen").to_zenodo()
    assert payload == {"person_or_org": {"type": "personal", "family_name": "Verstraelen"}}


def test_metadata_publication_date_today():
    """A record that is not published yet gets today's date, the only sensible guess."""
    metadata = _metadata(license=["mit"], resource_type="dataset")
    today = dt.date.today().isoformat()
    assert metadata.to_zenodo(DESCRIPTION)["publication_date"] == today
    assert metadata.to_zenodo(DESCRIPTION, None)["publication_date"] == today


def test_metadata_publication_date_given():
    """The publication date of a published record is sent back unchanged."""
    metadata = _metadata(license=["mit"], resource_type="dataset")
    payload = metadata.to_zenodo(DESCRIPTION, PUBLICATION_DATE)
    assert payload["publication_date"] == PUBLICATION_DATE


def test_refresh_existing_record_published_without_publication_date(tmp_path):
    """A published record that carries no date is dated today, instead of failing."""
    config = _config_with_version(tmp_path, "1.0.0")
    record = _published(7, "1.0.0")
    del record["metadata"]["publication_date"]
    zenodo = _FakeZenodo(record)
    _refresh_existing_record(zenodo, "7", config, DESCRIPTION, [])
    assert ("update_metadata", "7", None) in zenodo.calls


def test_describe_version():
    assert _describe_version(_published(7, "1.0.0")) == "version 1.0.0"
    assert _describe_version({"id": 7, "metadata": {}}) == "no version"


def _published_without_version(rid, is_latest=True) -> dict:
    """Build a published record that carries no version, as Zenodo allows."""
    record = _published(rid, "unused", is_latest=is_latest)
    del record["metadata"]["version"]
    return record


def test_refresh_existing_record_published_without_version(tmp_path):
    """A published record without a version never matches the local one, so a version is added.

    This is the record of someone who deposited it through the Zenodo web interface,
    where the version is an optional field, before adopting `srr-sync-zenodo`.
    """
    config = _config_with_version(tmp_path, "1.0.0")
    zenodo = _FakeZenodo(_published_without_version(7))
    _refresh_existing_record(zenodo, "7", config, DESCRIPTION, [])
    assert ("create_new_version", "7") in zenodo.calls


def test_check_version_chain_stale_record_without_version(tmp_path):
    """A version chain holding a record without a version is described without a KeyError."""
    config = _config_with_version(tmp_path, "1.0.0")
    versions = [_published_without_version(7, is_latest=False), _published_without_version(8)]
    zenodo = _FakeZenodo(versions[0], versions)
    with pytest.raises(ZenodoError) as exc_info:
        _refresh_existing_record(zenodo, "7", config, DESCRIPTION, [])
    assert "Record 7 (no version)" in str(exc_info.value)
    assert "record 8 (no version)" in str(exc_info.value)


def test_start_uploads_declares_every_file(tmp_path):
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest([])
    files = [_local_file(tmp_path, "one.txt", "hello"), _local_file(tmp_path, "two.txt", "bye")]
    zenodo.start_uploads("7", files)
    assert zenodo.rest.posted == [
        ("records/7/draft/files", [{"key": "one.txt"}, {"key": "two.txt"}])
    ]


def test_create_new_record_with_files(tmp_path):
    """A new record is created without files, which are then uploaded before the metadata."""
    file = _local_file(tmp_path, "one.txt", "hello")
    config = _config_with_version(tmp_path, "1.0.0")
    zenodo = _FakeZenodo(_v1_record(7, {}))
    _upload_new_record(zenodo, config, DESCRIPTION, [file])
    assert zenodo.calls == [
        ("create_new_record",),
        ("start_uploads", ["one.txt"]),
        ("upload_file", "one.txt"),
        ("update_metadata", "7", None),
    ]
    assert config.path_record_id.read_text(encoding="utf-8").strip() == "7"


def test_create_new_record_failed_upload(tmp_path):
    """A failed upload leaves a draft that the next run completes, not an orphan.

    The record id is therefore stored before the first file is uploaded.
    """
    file = _local_file(tmp_path, "one.txt", "hello")
    config = _config_with_version(tmp_path, "1.0.0")
    zenodo = _FakeZenodo(_v1_record(7, {}))

    def fail(rid, file):
        raise RESTError("Failed PUT https://zenodo.org/api/records/7/draft/files: 500")

    zenodo.upload_file = fail
    with pytest.raises(RESTError):
        _upload_new_record(zenodo, config, DESCRIPTION, [file])
    assert config.path_record_id.read_text(encoding="utf-8").strip() == "7"


def test_create_new_record_without_preview(tmp_path):
    """A new record has no files yet, so it is created without a default preview."""
    config = _config_with_version(tmp_path, "1.0.0")
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest([])
    zenodo.create_new_record(config, DESCRIPTION)
    assert zenodo.rest.posted[0][0] == "records"
    assert zenodo.rest.posted[0][1]["files"] == {"enabled": True}


@pytest.mark.parametrize(("names", "expected"), [(["two.txt", "one.txt"], "two.txt"), ([], None)])
def test_config_to_zenodo_preview(tmp_path, names, expected):
    """No file order is sent, because Zenodo drops it, and the first file is the preview."""
    config = _config_with_version(tmp_path, "1.0.0")
    files = [_local_file(tmp_path, name, name) for name in names]
    payload = config.to_zenodo(DESCRIPTION, files)
    files_options = {"enabled": True}
    if expected is not None:
        files_options["default_preview"] = expected
    assert payload["files"] == files_options


class _FakeGetRest:
    """A `RESTWrapper` stub that serves the records it holds and refuses every other address."""

    def __init__(self, records: dict[str, dict], status_code: int | None = 404):
        self.records = records
        self.status_code = status_code
        self.calls = []

    def get(self, loc):
        self.calls.append(loc)
        if loc not in self.records:
            raise RESTError(f"Failed GET {loc}: {self.status_code}", self.status_code)
        return self.records[loc]


def test_get_record_draft_first():
    """The draft carries the changes that are not published yet, so it is preferred."""
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeGetRest({"records/7/draft": {"id": 7, "is_published": False}})
    assert zenodo.get_record("7") == {"id": 7, "is_published": False}
    assert zenodo.rest.calls == ["records/7/draft"]


def test_get_record_published_without_draft():
    """A record without a draft is read as a published one."""
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeGetRest({"records/7": {"id": 7, "is_published": True}})
    assert zenodo.get_record("7") == {"id": 7, "is_published": True}
    assert zenodo.rest.calls == ["records/7/draft", "records/7"]


@pytest.mark.parametrize("status_code", [401, 403, 429, 500, 502, None])
def test_get_record_other_error(status_code):
    """A refused or lost request is not mistaken for a record without a draft."""
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeGetRest({}, status_code)
    with pytest.raises(RESTError) as exc_info:
        zenodo.get_record("7")
    assert exc_info.value.status_code == status_code
    assert zenodo.rest.calls == ["records/7/draft"]


def test_refresh_existing_record_published_new_version_with_files(tmp_path):
    """A new version created from a published record gets the files and then the metadata."""
    file = _local_file(tmp_path, "two.txt", "world")
    config = _config_with_version(tmp_path, "1.1.0")
    zenodo = _FakeZenodo(_published(7, "1.0.0"))
    _refresh_existing_record(zenodo, "7", config, DESCRIPTION, [file])
    assert zenodo.calls == [
        ("get_record", "7"),
        ("get_versions", "7"),
        ("create_new_version", "7"),
        ("start_uploads", ["two.txt"]),
        ("upload_file", "two.txt"),
        ("update_metadata", "7", None),
    ]


def test_related_scheme_invalid_message():
    """An unknown scheme is reported with the schemes Zenodo knows, not with their validators."""
    with pytest.raises(ValueError) as exc_info:
        Related(scheme="DOI", identifier="10.5281/zenodo.1", relation_type="cites")
    message = _format_error(exc_info.value, str)
    assert "Unknown identifier scheme for 'scheme': 'DOI'" in message
    assert "doi" in message
    assert "function" not in message


def test_access_invalid_message():
    """A value outside a fixed set is reported without the attrs internals of the validator."""
    with pytest.raises(ValueError) as exc_info:
        Access(files="hidden")
    message = _format_error(exc_info.value, str)
    assert message == "'files' must be in ['public', 'restricted'] (got 'hidden')"


def test_access_record_removed():
    """Zenodo refuses restricted records, so the record access level is not configurable."""
    with pytest.raises(TypeError):
        Access(record="public")
    assert Access(files="restricted").to_zenodo() == {"record": "public", "files": "restricted"}


def test_config_string_where_a_list_of_sections_belongs(tmp_path):
    """A string where a list of sections belongs is refused once, not once per character."""
    text = CONFIG_YAML[: CONFIG_YAML.find("  creators:")] + "  creators: Toon Verstraelen\n"
    with pytest.raises(ClassValidationError) as exc_info:
        _write_config(tmp_path, "sync_zenodo.yaml", text)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert messages == [
        "Expected a list of mappings, got str: 'Toon Verstraelen'. @ $.metadata.creators"
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("  creators:\n    - Toon Verstraelen\n", "got str: 'Toon Verstraelen'"),
        ("  creators:\n    - null\n", "got NoneType: None"),
    ],
)
def test_config_scalar_where_a_section_belongs(tmp_path, text, expected):
    """A scalar where a section belongs names the type of the value, not a missing method."""
    text = CONFIG_YAML[: CONFIG_YAML.find("  creators:")] + text
    with pytest.raises(ClassValidationError) as exc_info:
        _write_config(tmp_path, "sync_zenodo.yaml", text)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any(
        f"Expected a mapping of keys to values, {expected}" in message for message in messages
    )


def test_award_identifiers_to_zenodo():
    """The identifiers of an award and of a meeting are written in the same way."""
    award = Award(title="A title", identifiers=[Identifier("https://example.org/award/1")])
    assert award.to_zenodo()["identifiers"] == [{"identifier": "https://example.org/award/1"}]


def test_award_identifier_invalid():
    with pytest.raises(ValueError):
        Award(title="A title", identifiers=[Identifier("not a doi", "doi")])


def test_config_endpoint_trailing_slash(tmp_path):
    """A trailing slash on the endpoint does not end up in the middle of an address."""
    text = CONFIG_YAML.replace(
        "endpoint: https://zenodo.org/api", "endpoint: https://zenodo.org/api/"
    )
    config = _write_config(tmp_path, "sync_zenodo.yaml", text)
    assert config.endpoint == "https://zenodo.org/api"


def test_get_all_pages_endless():
    """A search result that never ends is refused instead of collected forever."""
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest([{"id": rid} for rid in range(SEARCH_PAGE_SIZE * MAX_SEARCH_PAGES + 1)])
    with pytest.raises(ZenodoError) as exc_info:
        zenodo.get_versions("3")
    assert f"{MAX_SEARCH_PAGES} full pages" in str(exc_info.value)
    assert len(zenodo.rest.calls) == MAX_SEARCH_PAGES


@pytest.mark.parametrize("entry", [{}, {"checksum": None}])
def test_entry_md5_without_checksum(entry):
    """A file entry without a checksum is reported as a message, not as a KeyError."""
    with pytest.raises(ZenodoError) as exc_info:
        _entry_md5(entry)
    assert "unexpected checksum format" in str(exc_info.value)


def test_upload_file_without_size(tmp_path):
    """A commit response without a size is reported as a message, not as a KeyError."""
    file = _local_file(tmp_path, "one.txt", "hello")
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakePutRest({})
    with pytest.raises(ZenodoError) as exc_info:
        zenodo.upload_file("7", file)
    assert "File size mismatch" in str(exc_info.value)


class _FakePutRest:
    """A `RESTWrapper` stub that accepts an upload and answers the commit with fixed data."""

    def __init__(self, commit: dict):
        self.commit = commit

    def put(self, loc, data):
        return None

    def post(self, loc):
        return self.commit


def test_record_url_without_link():
    """A record without a link to the website is shown with its address in the API."""
    zenodo = ZenodoWrapper("token", "https://zenodo.org/api")
    assert _record_url(zenodo, {"id": 7}) == "https://zenodo.org/api/records/7"


def test_record_url_with_link():
    zenodo = ZenodoWrapper("token")
    record = {"id": 7, "links": {"self_html": "https://zenodo.org/records/7"}}
    assert _record_url(zenodo, record) == "https://zenodo.org/records/7"


def test_record_id_missing():
    """A record without an id is reported as a message, not as a KeyError."""
    with pytest.raises(ZenodoError) as exc_info:
        _record_id({"metadata": {}})
    assert INVENIORDM_MIMETYPE in str(exc_info.value)


def test_write_record_id_creates_parent(tmp_path):
    path = Path(tmp_path) / "sub" / "dir" / "record_id.txt"
    _write_record_id(path, "7")
    assert path.read_text(encoding="utf-8") == "7\n"


def test_write_record_id_without_parent(tmp_path, monkeypatch):
    """A bare file name has no parent directory to create."""
    monkeypatch.chdir(tmp_path)
    _write_record_id(Path("record_id.txt"), "7")
    assert Path("record_id.txt").read_text(encoding="utf-8") == "7\n"


def test_write_record_id_unwritable(tmp_path):
    """A record that exists on Zenodo but cannot be recorded locally is reported, not raised raw."""
    path = Path(tmp_path) / "record_id.txt"
    path.mkdir()
    with pytest.raises(ZenodoError, match="Cannot write the record ID file"):
        _write_record_id(path, "7")


def test_write_record_id_unwritable_parent(tmp_path):
    path = Path(tmp_path) / "blocked"
    path.write_text("not a directory", encoding="utf-8")
    with pytest.raises(ZenodoError, match="Cannot write the record ID file"):
        _write_record_id(path / "record_id.txt", "7")


def test_update_online_empty_record_id(tmp_path):
    """An empty record id file is reported as a message, instead of creating a second record."""
    config = _config_with_version(tmp_path, "1.0.0")
    config.path_record_id.write_text("\n", encoding="utf-8")
    with pytest.raises(ZenodoError) as exc_info:
        _update_online(_FakeZenodo(), config, DESCRIPTION, [])
    assert "is empty" in str(exc_info.value)


@pytest.mark.parametrize("extra", [[], ["--dry-run"]])
def test_main_missing_file(tmp_path, monkeypatch, capsys, extra):
    """A file that does not exist is reported before Zenodo is contacted.

    The real `amend()` is used, which refuses a missing input outside a StepUp step.
    """
    monkeypatch.setattr("stepup.reprep.sync_zenodo.amend", stepup.core.api.amend)
    monkeypatch.setenv("REPREP_ZENODO_TOKEN", "token")
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML, encoding="utf-8", newline="\n")
    path_inventory = _write_inventory(tmp_path, [UploadFile(tmp_path / "nope.txt", "0" * 32)])
    assert main([str(path), _write_description(tmp_path), path_inventory, *extra]) == 1
    captured = capsys.readouterr()
    assert "do not exist" in captured.err
    assert "Traceback" not in captured.err


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project in the current directory, with one file to upload and an up-to-date inventory.

    The config file names a relative record id file, as in a real project,
    and `REPREP_ZENODO_TOKEN` is set, so that every test chooses what it unsets.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("REPREP_ZENODO_TOKEN", "token")
    Path("sync_zenodo.yaml").write_text(CONFIG_YAML, encoding="utf-8")
    Path("zenodo_description.md").write_text("A *dataset*.\n", encoding="utf-8")
    Path("README.txt").write_text("hello", encoding="utf-8")
    _write_inventory_file("zenodo_inventory.jsonl", [UploadFile("README.txt", _md5("hello"))])


SYNC_ARGS = [
    "sync_zenodo.yaml",
    "zenodo_description.md",
    "zenodo_inventory.jsonl",
    "--no-check-md5",
]
"""The arguments of `srr-sync-zenodo` in a workflow, for the `project` fixture."""

BY_HAND_ARGS = ["sync_zenodo.yaml", "zenodo_description.md", "zenodo_inventory.jsonl"]
"""The arguments of `srr-sync-zenodo` when run by hand, for the `project` fixture."""


def _use_fake_zenodo(monkeypatch, zenodo: _FakeZenodo) -> list[str]:
    """Let `main` talk to a fake Zenodo.

    Returns
    -------
    endpoints
        The endpoint of every connection to Zenodo that `main` made, in the order of creation.
    """
    endpoints = []

    def connect(token, endpoint, verbose=False):
        endpoints.append(endpoint)
        return zenodo

    monkeypatch.setattr("stepup.reprep.sync_zenodo.ZenodoWrapper", connect)
    return endpoints


@pytest.fixture
def no_hashing(monkeypatch):
    """Make every computation of an MD5 checksum in `srr-sync-zenodo` fail."""

    def fail(path):
        raise AssertionError(f"Unexpected MD5 computation of {path}")

    monkeypatch.setattr("stepup.reprep.sync_zenodo._compute_md5", fail)


def _draft(checksums: dict[str, str | None]) -> dict:
    """Build the draft record of the `project` fixture, with the given files on Zenodo."""
    return _v1_record(7, checksums, is_published=False, metadata={"version": "1.0.0"})


@pytest.mark.usefixtures("project", "no_hashing")
def test_sequence_first_build(monkeypatch):
    zenodo = _FakeZenodo()
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(SYNC_ARGS) == 0
    assert zenodo.calls == [
        ("create_new_record",),
        ("start_uploads", ["README.txt"]),
        ("upload_file", "README.txt"),
        ("update_metadata", "7", None),
    ]
    assert Path(".zenodo-record-id.txt").read_text(encoding="utf-8") == "7\n"


@pytest.mark.usefixtures("project", "no_hashing")
def test_sequence_nothing_changed(monkeypatch):
    """Nothing is uploaded or hashed, and the metadata is sent again."""
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    zenodo = _FakeZenodo(_draft({"README.txt": _md5("hello")}))
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(SYNC_ARGS) == 0
    assert zenodo.calls == [
        ("get_record", "7"),
        ("update_metadata", "7", None),
    ]


@pytest.mark.usefixtures("project", "no_hashing")
def test_sequence_local_file_changed(monkeypatch):
    """The inventory step wrote a new checksum, so the sync replaces the file."""
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    Path("README.txt").write_text("changed", encoding="utf-8")
    _write_inventory_file("zenodo_inventory.jsonl", [UploadFile("README.txt", _md5("changed"))])
    zenodo = _FakeZenodo(_draft({"README.txt": _md5("hello")}))
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(SYNC_ARGS) == 0
    assert zenodo.calls == [
        ("get_record", "7"),
        ("delete_file", "README.txt"),
        ("start_uploads", ["README.txt"]),
        ("upload_file", "README.txt"),
        ("update_metadata", "7", None),
    ]


@pytest.mark.parametrize(
    ("checksums", "uploads"),
    [
        ({}, [("start_uploads", ["README.txt"]), ("upload_file", "README.txt")]),
        (
            {"README.txt": _md5("edited online")},
            [
                ("delete_file", "README.txt"),
                ("start_uploads", ["README.txt"]),
                ("upload_file", "README.txt"),
            ],
        ),
    ],
)
@pytest.mark.usefixtures("project", "no_hashing")
def test_sequence_draft_changed_by_hand(monkeypatch, checksums, uploads):
    """A file deleted or changed in the draft by hand is uploaded again without a local change."""
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    zenodo = _FakeZenodo(_draft(checksums))
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(SYNC_ARGS) == 0
    assert zenodo.calls == [
        ("get_record", "7"),
        *uploads,
        ("update_metadata", "7", None),
    ]


@pytest.mark.usefixtures("project", "no_hashing")
def test_sequence_published_in_web_interface(monkeypatch):
    """The files are compared with the inventory and the metadata is published again."""
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    zenodo = _FakeZenodo(_published(7, "1.0.0", {"README.txt": _md5("hello")}))
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(SYNC_ARGS) == 0
    assert zenodo.calls == [
        ("get_record", "7"),
        ("get_versions", "7"),
        ("edit_record", "7"),
        ("update_metadata", "7", PUBLICATION_DATE),
        ("publish_record", "7"),
    ]


@pytest.mark.usefixtures("project", "no_hashing")
def test_sequence_published_changed_locally(monkeypatch, capsys):
    """A published file that differs from the inventory asks for a new version."""
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    zenodo = _FakeZenodo(_published(7, "1.0.0", {"README.txt": _md5("bye")}))
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(SYNC_ARGS) == 1
    assert "MD5 checksum mismatch for README.txt (1.0.0, published)" in capsys.readouterr().err
    assert ("publish_record", "7") not in zenodo.calls


@pytest.mark.usefixtures("project")
def test_sequence_unreachable(monkeypatch, capsys):
    """A sync with a token fails when Zenodo cannot be reached."""
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    zenodo = _FakeZenodo()

    def fail(rid):
        raise RESTError("Failed GET https://zenodo.org/api/records/7/draft: Connection refused")

    zenodo.get_record = fail
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(SYNC_ARGS) == 1
    assert "Connection refused" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("token", "expected"),
    [(None, "is not set"), ("", "is empty")],
)
@pytest.mark.usefixtures("project")
def test_sequence_without_token(monkeypatch, capsys, token, expected):
    """Without a token, or with an empty one, the sync warns and sends nothing."""
    if token is None:
        monkeypatch.delenv("REPREP_ZENODO_TOKEN")
    else:
        monkeypatch.setenv("REPREP_ZENODO_TOKEN", token)
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    assert main(SYNC_ARGS) == 0
    assert f"The REPREP_ZENODO_TOKEN environment variable {expected}." in capsys.readouterr().out
    assert endpoints == []


@pytest.mark.parametrize("token", [None, "token"])
@pytest.mark.usefixtures("project")
def test_sequence_offline(monkeypatch, capsys, token):
    """An offline build sends nothing, with or without a token, and does not warn about it."""
    monkeypatch.setenv("STEPUP_BUILD_OFFLINE", "1")
    if token is None:
        monkeypatch.delenv("REPREP_ZENODO_TOKEN")
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    assert main(SYNC_ARGS) == 0
    out = capsys.readouterr().out
    assert "The build is offline (STEPUP_BUILD_OFFLINE=1)." in out
    assert "REPREP_ZENODO_TOKEN" not in out
    assert endpoints == []


@pytest.mark.usefixtures("project")
def test_sequence_online_explicitly(monkeypatch):
    """Any other value of `STEPUP_BUILD_OFFLINE` than `1` is online."""
    monkeypatch.setenv("STEPUP_BUILD_OFFLINE", "0")
    zenodo = _FakeZenodo()
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(SYNC_ARGS) == 0
    assert zenodo.calls[0] == ("create_new_record",)


@pytest.mark.usefixtures("project")
def test_sequence_offline_description_in_config(monkeypatch, capsys):
    """The configuration is validated before the sync finds that it is offline.

    The description has its own file, so the config file cannot hold one.
    """
    monkeypatch.setenv("STEPUP_BUILD_OFFLINE", "1")
    text = CONFIG_YAML.replace(
        "  title: 'A title'\n", "  title: 'A title'\n  description: 'Text'\n"
    )
    Path("sync_zenodo.yaml").write_text(text, encoding="utf-8")
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    assert main(SYNC_ARGS) == 1
    err = capsys.readouterr().err
    assert "metadata" in err
    assert "description" in err
    assert endpoints == []


@pytest.mark.parametrize("env", [{"STEPUP_BUILD_OFFLINE": "1"}, {"REPREP_ZENODO_TOKEN": ""}])
@pytest.mark.usefixtures("project")
def test_sequence_invalid_inventory_before_early_exit(monkeypatch, capsys, env):
    """Every run reports an inventory that cannot be used, also when it would exit early."""
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    Path("zenodo_inventory.jsonl").write_text("{}", encoding="utf-8")
    assert main(SYNC_ARGS) == 1
    assert "is not an inventory written by" in capsys.readouterr().err


@pytest.mark.usefixtures("project")
def test_sequence_by_hand_stale_inventory(monkeypatch, capsys):
    """A run by hand after a local change without a new inventory stops before contacting Zenodo."""
    Path("README.txt").write_text("changed", encoding="utf-8")
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    assert main(BY_HAND_ARGS) == 1
    err = capsys.readouterr().err
    assert "The file README.txt has changed after the inventory zenodo_inventory.jsonl" in err
    assert "`stepup build`" in err
    assert "`srr-make-inventory`" in err
    assert endpoints == []


@pytest.mark.usefixtures("project")
def test_sequence_by_hand_up_to_date(monkeypatch):
    """A run by hand with an up-to-date inventory syncs as in the workflow."""
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    zenodo = _FakeZenodo(_draft({"README.txt": _md5("hello")}))
    _use_fake_zenodo(monkeypatch, zenodo)
    assert main(BY_HAND_ARGS) == 0
    assert zenodo.calls == [
        ("get_record", "7"),
        ("update_metadata", "7", None),
    ]


@pytest.mark.usefixtures("project")
def test_sequence_dry_run_skips_md5_check(monkeypatch, capsys):
    """A dry run reads the inventory but checks no MD5 checksums."""
    Path("README.txt").write_text("changed", encoding="utf-8")
    assert main([*BY_HAND_ARGS, "--dry-run"]) == 0
    assert '"default_preview": "README.txt"' in capsys.readouterr().out


OLD_DESCRIPTION_OPTION = "--description=zenodo_description.md"
"""The option of StepUp RepRep 4.1 for the description, which is now a positional argument."""


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], "the following arguments are required: description, inventory"),
        ([OLD_DESCRIPTION_OPTION], "the following arguments are required: description, inventory"),
        (["README.txt"], "the following arguments are required: inventory"),
        (["README.txt", OLD_DESCRIPTION_OPTION], "the following arguments are required: inventory"),
        (["README.txt", "data.json", OLD_DESCRIPTION_OPTION], "unrecognized arguments"),
    ],
)
@pytest.mark.usefixtures("project")
def test_old_command_line_argparse(monkeypatch, capsys, args, expected):
    """The command line of StepUp RepRep 4.1, `srr-sync-zenodo CONFIG PATHS...`, is refused.

    Most variants are refused by `argparse`, before Zenodo is contacted.
    """
    Path("data.json").write_text('{"temperature": 300}\n', encoding="utf-8")
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    with pytest.raises(SystemExit) as exc_info:
        main(["sync_zenodo.yaml", *args])
    assert exc_info.value.code == 2
    assert expected in capsys.readouterr().err
    assert endpoints == []


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (["README.txt", "data.json"], "must be a Markdown (.md) or HTML (.html) file"),
        (["README.md", "data.json"], "The file data.json is not an inventory written by"),
    ],
)
@pytest.mark.usefixtures("project")
def test_old_command_line_two_files(monkeypatch, capsys, paths, expected):
    """The command line of StepUp RepRep 4.1 with two files reads them as description and inventory.

    Neither is accepted, which is found before Zenodo is contacted.
    """
    Path("README.md").write_text("A *dataset*.\n", encoding="utf-8")
    Path("data.json").write_text('{"temperature": 300}\n', encoding="utf-8")
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    assert main(["sync_zenodo.yaml", *paths]) == 1
    err = capsys.readouterr().err
    assert expected in err
    # The message must not suggest writing an inventory over the data file.
    assert "Write it again" not in err
    assert "Traceback" not in err
    assert endpoints == []


def test_upload_file_inventory_md5(tmp_path, no_hashing):
    """An upload is checked against the inventory, without hashing the local file."""
    file = _local_file(tmp_path, "one.txt", "hello")
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakePutRest({"size": 5, "checksum": f"md5:{_md5('hello')}"})
    zenodo.upload_file("7", file)


def test_upload_file_stale_inventory(tmp_path):
    """A file that changed after the inventory was written is caught when it is uploaded."""
    path = Path(tmp_path) / "one.txt"
    path.write_text("bye!!", encoding="utf-8")
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakePutRest({"size": 5, "checksum": f"md5:{_md5('bye!!')}"})
    with pytest.raises(ZenodoError) as exc_info:
        zenodo.upload_file("7", UploadFile(path, _md5("hello")))
    assert f"MD5 checksum mismatch for {path}, inventory {_md5('hello')}" in str(exc_info.value)


@pytest.mark.parametrize(
    "env",
    [{}, {"STEPUP_BUILD_OFFLINE": "1"}, {"REPREP_ZENODO_TOKEN": ""}, {"REPREP_ZENODO_TOKEN": None}],
)
@pytest.mark.parametrize("extra", [[], ["--dry-run"]])
@pytest.mark.usefixtures("project")
def test_sequence_amend_before_early_exit(monkeypatch, amended, env, extra):
    """The files are amended as inputs in every run, so the workflow graph is always the same."""
    for name, value in env.items():
        if value is None:
            monkeypatch.delenv(name)
        else:
            monkeypatch.setenv(name, value)
    Path(".zenodo-record-id.txt").write_text("7\n", encoding="utf-8")
    _use_fake_zenodo(monkeypatch, _FakeZenodo(_draft({"README.txt": _md5("hello")})))
    assert main([*SYNC_ARGS, *extra]) == 0
    assert amended == [[Path("README.txt")]]


@pytest.mark.usefixtures("project")
def test_sequence_input_not_found(monkeypatch):
    """A file that StepUp still has to build defers the step instead of failing it."""

    def amend(inp=()):
        raise InputNotFoundError("Dynamic inputs are not available yet.")

    monkeypatch.setattr("stepup.reprep.sync_zenodo.amend", amend)
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    with pytest.raises(InputNotFoundError):
        main(SYNC_ARGS)
    assert endpoints == []


@pytest.mark.parametrize("algorithm", ["sha256", "sha1"])
@pytest.mark.usefixtures("project")
def test_sequence_md5_required(monkeypatch, capsys, algorithm):
    """An inventory with other digests is refused, because Zenodo reports MD5 checksums."""
    write_inventory(
        "zenodo_inventory.jsonl", ["README.txt"], hash_algorithm=algorithm, do_amend=False
    )
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    assert main([*SYNC_ARGS, "--dry-run"]) == 1
    err = capsys.readouterr().err
    assert f"has {algorithm} digests" in err
    assert "`srr-make-inventory --hash md5`" in err
    assert endpoints == []


@needs_symlinks
@pytest.mark.usefixtures("project")
def test_sequence_link_refused(monkeypatch, capsys):
    """A symbolic link cannot be uploaded, because Zenodo has no links."""
    Path("README.md").symlink_to("README.txt")
    write_inventory("zenodo_inventory.jsonl", ["README.txt", "README.md"], do_amend=False)
    endpoints = _use_fake_zenodo(monkeypatch, _FakeZenodo())
    assert main([*SYNC_ARGS, "--dry-run"]) == 1
    err = capsys.readouterr().err
    assert "lists the symbolic link README.md" in err
    assert endpoints == []


@pytest.mark.usefixtures("project")
def test_sequence_paths_relative_to_inventory(monkeypatch, capsys, amended):
    """The paths in the inventory are relative to its parent directory."""
    Path("data").mkdir()
    Path("data/one.txt").write_text("one", encoding="utf-8")
    write_inventory("data/zenodo_inventory.jsonl", ["data/one.txt", "README.txt"], do_amend=False)
    args = ["sync_zenodo.yaml", "zenodo_description.md", "data/zenodo_inventory.jsonl"]
    Path("README.txt").write_text("changed", encoding="utf-8")
    assert main(args) == 1
    assert "The file README.txt has changed" in capsys.readouterr().err
    assert amended == [[Path("data/one.txt"), Path("README.txt")]]
    write_inventory("data/zenodo_inventory.jsonl", ["data/one.txt", "README.txt"], do_amend=False)
    assert main([*args, "--dry-run"]) == 0
    out = capsys.readouterr().out
    payload = json.loads(out[out.find("{") :])
    assert payload["files"]["default_preview"] == "one.txt"


@pytest.mark.usefixtures("project")
def test_sequence_same_name(monkeypatch, capsys):
    """Two files with the same name cannot be uploaded to one record."""
    Path("data").mkdir()
    Path("data/README.txt").write_text("other", encoding="utf-8")
    write_inventory("zenodo_inventory.jsonl", ["README.txt", "data/README.txt"], do_amend=False)
    assert main([*SYNC_ARGS, "--dry-run"]) == 1
    err = capsys.readouterr().err
    assert "The inventory zenodo_inventory.jsonl cannot be used" in err
    assert "files must have different names" in err


def test_check_zenodo_limits_ok():
    files = [UploadFile("one.txt", "0" * 32), UploadFile("sub/two.txt", "0" * 32)]
    _check_zenodo_limits(files, Path("inventory.jsonl"))


def test_check_zenodo_limits_same_name_other_directory():
    files = [UploadFile("sub1/one.txt", "0" * 32), UploadFile("sub2/one.txt", "0" * 32)]
    with pytest.raises(ZenodoError) as exc_info:
        _check_zenodo_limits(files, Path("inventory.jsonl"))
    assert "The name one.txt is used by sub1/one.txt and sub2/one.txt." in str(exc_info.value)


def test_check_zenodo_limits_too_many():
    files = [UploadFile(f"file{i}.txt", "0" * 32) for i in range(MAX_NUM_ZENODO_FILES)]
    _check_zenodo_limits(files, Path("inventory.jsonl"))
    with pytest.raises(ZenodoError, match=f"at most {MAX_NUM_ZENODO_FILES} files"):
        _check_zenodo_limits([*files, UploadFile("extra.txt", "0" * 32)], Path("inventory.jsonl"))


@pytest.mark.usefixtures("project")
def test_sequence_inventory_missing(monkeypatch, capsys):
    Path("zenodo_inventory.jsonl").remove()
    assert main([*SYNC_ARGS, "--dry-run"]) == 1
    err = capsys.readouterr().err
    assert "The inventory zenodo_inventory.jsonl does not exist" in err
    assert "`srr-make-inventory`" in err
