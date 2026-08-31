# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.sync_zenodo."""

import datetime
import hashlib
import json
from importlib import resources

import cattrs
import pytest
import yaml
from cattrs.errors import ClassValidationError
from path import Path

from stepup.reprep.sync_zenodo import (
    INVENIORDM_MIMETYPE,
    SEARCH_PAGE_SIZE,
    VOCABULARIES_FILENAME,
    Config,
    Creator,
    CustomFields,
    Imprint,
    Journal,
    Meeting,
    MeetingIdentifier,
    Metadata,
    Related,
    RESTError,
    Thesis,
    ZenodoError,
    ZenodoWrapper,
    _check_record_md5,
    _check_version_chain,
    _clean_online,
    _describe_version,
    _format_error,
    _get_record_files,
    _get_record_version,
    _load_config_data,
    _load_vocabularies,
    _make_converter,
    _parse_args,
    _record_publication_date,
    _refresh_existing_record,
    _refresh_files,
    _search_hits,
    _upload_new_record,
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
            MeetingIdentifier("10.5281/zenodo.1234567", "doi"),
            MeetingIdentifier("https://example.org/icc24/proceedings"),
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
            identifiers=[MeetingIdentifier("10.5281/zenodo.1234567", "doi")],
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
        MeetingIdentifier("10.5281/zenodo.1234567", scheme)


def test_custom_fields_meeting_identifier_scheme_mismatch():
    with pytest.raises(ValueError):
        MeetingIdentifier("not a doi", "doi")


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


VOCABULARY_NAMES = [
    "_date",
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


@pytest.mark.parametrize("name", VOCABULARY_NAMES[1:])
def test_vocabularies_data_file_sorted_and_unique(name):
    """Guard against a hand edit that the refresh script would have prevented."""
    text = resources.files("stepup.reprep").joinpath(VOCABULARIES_FILENAME).read_text()
    identifiers = yaml.safe_load(text)[name]
    assert all(isinstance(identifier, str) for identifier in identifiers)
    assert identifiers == sorted(set(identifiers))


def _metadata(**kwargs) -> Metadata:
    kwargs.setdefault("title", "A title")
    kwargs.setdefault("version", "1.0.0")
    kwargs.setdefault("creators", [Creator("Verstraelen", "Toon")])
    kwargs.setdefault("publisher", "Zenodo")
    return Metadata(**kwargs)


@pytest.mark.parametrize("identifier", ["dataset", "software", "publication-article"])
def test_metadata_resource_type_valid(identifier):
    metadata = _metadata(license=["cc-by-4.0"], resource_type=identifier)
    assert metadata.to_zenodo()["resource_type"] == {"id": identifier}


@pytest.mark.parametrize("identifier", ["Dataset", "DATASET", "datasets", "audio", ""])
def test_metadata_resource_type_invalid(identifier):
    with pytest.raises(ValueError):
        _metadata(license=["cc-by-4.0"], resource_type=identifier)


@pytest.mark.parametrize("identifier", ["cc-by-4.0", "cc-by-nc-4.0", "mit", "CC-BY-4.0"])
def test_metadata_license_valid(identifier):
    """The license is lowercased before it is validated."""
    metadata = _metadata(license=[identifier], resource_type="dataset")
    assert metadata.to_zenodo()["rights"] == [{"id": identifier.lower()}]


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
    args = _parse_args(["sync_zenodo.yaml"])
    assert args.config == "sync_zenodo.yaml"
    assert args.paths == []
    assert args.description is None
    assert args.verbose is False
    assert args.clean is False
    assert args.dry_run is False


def test_parse_args_all():
    args = _parse_args(
        [
            "sync_zenodo.toml",
            "one.txt",
            "sub/two.txt",
            "--description=zenodo_description.md",
            "--verbose",
            "--clean",
            "--dry-run",
        ]
    )
    assert args.config == "sync_zenodo.toml"
    assert args.paths == ["one.txt", "sub/two.txt"]
    assert args.description == "zenodo_description.md"
    assert args.verbose is True
    assert args.clean is True
    assert args.dry_run is True


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
    path.write_text(text)
    return _make_converter().structure(_load_config_data(path), Config)


def test_config_formats_equivalent(tmp_path):
    """The same configuration in YAML, JSON and TOML produces the same Zenodo payload."""
    configs = [
        _write_config(tmp_path, "sync_zenodo.yaml", CONFIG_YAML),
        _write_config(tmp_path, "sync_zenodo.json", CONFIG_JSON),
        _write_config(tmp_path, "sync_zenodo.toml", CONFIG_TOML),
    ]
    payloads = [config.to_zenodo([]) for config in configs]
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
    path.write_text(text)
    with pytest.raises(ClassValidationError) as exc_info:
        _make_converter().structure(_load_config_data(path), Config)
    messages = cattrs.transform_error(exc_info.value, format_exception=_format_error)
    assert any("Enclose the value in quotes" in message for message in messages)


def test_load_config_data_unknown_suffix(tmp_path):
    path = tmp_path / "sync_zenodo.ini"
    path.write_text("[metadata]\n")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "suffix" in str(exc_info.value)
    assert ".toml" in str(exc_info.value)


def test_load_config_data_legacy_zenodo_json(tmp_path):
    path = tmp_path / ".zenodo.json"
    path.write_text('{"title": "A title"}\n')
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "GitHub release" in str(exc_info.value)


def test_load_config_data_not_a_mapping(tmp_path):
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text("- one\n- two\n")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "mapping" in str(exc_info.value)


def test_load_config_data_syntax_error(tmp_path):
    """A config file the parser chokes on is reported without the traceback of the parser."""
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text("metadata: [unclosed\n")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "Cannot read the config file" in str(exc_info.value)


def test_load_config_data_missing(tmp_path):
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(tmp_path / "absent.yaml")
    assert "Cannot read the config file" in str(exc_info.value)


def test_load_config_data_empty(tmp_path):
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text("")
    with pytest.raises(ZenodoError) as exc_info:
        _load_config_data(path)
    assert "empty" in str(exc_info.value)


def test_config_endpoint_default(tmp_path):
    text = CONFIG_YAML.replace("endpoint: https://zenodo.org/api\n", "")
    config = _write_config(tmp_path, "sync_zenodo.yaml", text)
    assert config.endpoint == "https://sandbox.zenodo.org/api"


@pytest.mark.parametrize("endpoint", ["zenodo.org/api", "https://zenodo", ""])
def test_config_endpoint_invalid(tmp_path, endpoint):
    text = CONFIG_YAML.replace("endpoint: https://zenodo.org/api", f"endpoint: '{endpoint}'")
    with pytest.raises(ClassValidationError):
        _write_config(tmp_path, "sync_zenodo.yaml", text)


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
    assert config.to_zenodo([]) == listed.to_zenodo([])


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


def test_main_dry_run(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("REPREP_ZENODO_TOKEN", raising=False)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML)
    assert main([str(path), "--dry-run"]) == 0
    out = capsys.readouterr().out
    # Pop the first line, which is just a message explaining the output below.
    out = out[out.find("{") :]
    payload = json.loads(out)
    assert payload["metadata"]["title"] == "A title"
    assert payload["files"] == {"enabled": False, "order": []}
    assert "endpoint" not in payload


def test_main_invalid_config(tmp_path, monkeypatch, capsys):
    """A config file that Zenodo would reject is reported without a traceback.

    Every problem is listed, because `cattrs` collects them all before it gives up.
    """
    monkeypatch.delenv("REPREP_ZENODO_TOKEN", raising=False)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(
        CONFIG_YAML.replace("version: '1.0.0'", "version: 1.0").replace("  publisher: Zenodo\n", "")
    )
    assert main([str(path), "--dry-run"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    # The message is reproduced verbatim, so `rich` does not wrap it at eighty columns.
    assert "Expected a string, got float: 1.0. Enclose the value in quotes" in captured.err
    assert "metadata.publisher" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["one.txt", "one.txt"], "Duplicate paths are not allowed"),
        (["--description=missing.md"], "Description file missing.md does not exist"),
        (["--description=notes.txt"], "must be a Markdown (.md) or HTML (.html) file"),
    ],
)
def test_main_user_error(tmp_path, monkeypatch, capsys, args, expected):
    """Everything the user can get wrong is reported as a message, not as a traceback."""
    monkeypatch.delenv("REPREP_ZENODO_TOKEN", raising=False)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML)
    assert main([str(path), *args, "--dry-run"]) == 1
    captured = capsys.readouterr()
    assert expected in captured.err
    assert "Traceback" not in captured.err


def test_main_rest_error(tmp_path, monkeypatch, capsys):
    """A request that Zenodo refuses is reported with the message of the response."""
    monkeypatch.setenv("REPREP_ZENODO_TOKEN", "token")
    # The record id file of the config is a relative path, so it must not land in the repository.
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "sync_zenodo.yaml"
    path.write_text(CONFIG_YAML)

    def fail(*args, **kwargs):
        raise RESTError("Failed POST https://zenodo.org/api/records: 400")

    monkeypatch.setattr(ZenodoWrapper, "create_new_record", fail)
    assert main([str(path)]) == 1
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
    assert metadata.to_zenodo()["publisher"] == "Ghent University"


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
    [("version", "1" * 192), ("version", ""), ("copyright", ""), ("description", "ab")],
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


def _v1_record(rid: int, checksums: dict[str, str], **kwargs) -> dict:
    """Build a record as Zenodo serializes it for `application/vnd.inveniordm.v1+json`."""
    return {
        "id": rid,
        "links": {"self_html": f"https://zenodo.org/record/{rid}"},
        "files": {
            "enabled": len(checksums) > 0,
            "order": [],
            "count": len(checksums),
            "total_bytes": 0,
            "entries": {
                name: {"key": name, "checksum": f"md5:{md5}", "size": 0}
                for name, md5 in checksums.items()
            },
        },
        **kwargs,
    }


def _write_file(tmp_path, name: str, content: str) -> Path:
    """Write a local file and return its path."""
    path = Path(tmp_path) / name
    path.write_text(content)
    return path


def _md5(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


class _FakeZenodo:
    """A `ZenodoWrapper` stub that records the calls made on it."""

    def __init__(self, record=None, versions=None):
        self.record = record
        self.versions = [record] if versions is None else versions
        self.calls = []

    def create_new_record(self, config):
        self.calls.append(("create_new_record",))
        if self.record is None:
            self.record = {"id": 7, "links": {"self_html": "https://zenodo.org/record/7"}}
        return self.record

    def get_record(self, rid):
        self.calls.append(("get_record", rid))
        return self.record

    def get_versions(self, rid):
        self.calls.append(("get_versions", rid))
        return self.versions

    def delete_file(self, rid, name):
        self.calls.append(("delete_file", name))

    def start_uploads(self, rid, paths):
        if len(paths) == 0:
            return
        self.calls.append(("start_uploads", [path.name for path in paths]))

    def upload_file(self, rid, path):
        self.calls.append(("upload_file", path.name))

    def update_metadata(self, rid, config, paths, publication_date=None):
        self.calls.append(("update_metadata", rid, publication_date))
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


class _FakeRest:
    """A `RESTWrapper` stub that serves a paginated search result."""

    def __init__(self, hits):
        self.hits = hits
        self.calls = []
        self.deleted = []
        self.posted = []

    def get(self, loc, params):
        self.calls.append((loc, params["page"]))
        page, size = params["page"], params["size"]
        return {
            "hits": {"hits": self.hits[(page - 1) * size : page * size], "total": len(self.hits)}
        }

    def delete(self, loc):
        self.deleted.append(loc)

    def post(self, loc, json):
        self.posted.append((loc, json))


@pytest.mark.parametrize("num", [0, 1, SEARCH_PAGE_SIZE, SEARCH_PAGE_SIZE + 1])
def test_get_versions_pagination(num):
    """The version chain is collected from all pages of the search result."""
    hits = [{"id": rid} for rid in range(num)]
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest(hits)
    assert zenodo.get_versions(3) == hits
    num_pages = num // SEARCH_PAGE_SIZE + 1
    assert zenodo.rest.calls == [("records/3/versions", page) for page in range(1, num_pages + 1)]


@pytest.mark.parametrize("num", [0, 1, SEARCH_PAGE_SIZE, SEARCH_PAGE_SIZE + 1])
def test_get_user_records_pagination(num):
    """The records of the user are collected from all pages of the search result.

    Zenodo serves this search result in pages of at most `SEARCH_PAGE_SIZE` records,
    so a user with more records than that has drafts beyond the first page.
    """
    hits = [{"id": rid} for rid in range(num)]
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest(hits)
    assert zenodo.get_user_records() == hits
    num_pages = num // SEARCH_PAGE_SIZE + 1
    assert zenodo.rest.calls == [("user/records", page) for page in range(1, num_pages + 1)]


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


def test_refresh_files_unchanged(tmp_path):
    path = _write_file(tmp_path, "one.txt", "hello")
    record = _v1_record(1, {"one.txt": _md5("hello")})
    zenodo = _FakeZenodo()
    assert not _refresh_files(zenodo, record, {"one.txt": path}, "1.0.0")
    assert zenodo.calls == []


def test_refresh_files_upload_new(tmp_path):
    path = _write_file(tmp_path, "one.txt", "hello")
    record = _v1_record(1, {})
    zenodo = _FakeZenodo()
    assert _refresh_files(zenodo, record, {"one.txt": path}, "1.0.0")
    assert zenodo.calls == [("start_uploads", ["one.txt"]), ("upload_file", "one.txt")]


def test_refresh_files_replace_changed(tmp_path):
    path = _write_file(tmp_path, "one.txt", "hello")
    record = _v1_record(1, {"one.txt": _md5("bye")})
    zenodo = _FakeZenodo()
    assert _refresh_files(zenodo, record, {"one.txt": path}, "1.0.0")
    assert zenodo.calls == [
        ("delete_file", "one.txt"),
        ("start_uploads", ["one.txt"]),
        ("upload_file", "one.txt"),
    ]


def test_refresh_files_delete_removed(tmp_path):
    record = _v1_record(1, {"gone.txt": _md5("hello")})
    zenodo = _FakeZenodo()
    assert _refresh_files(zenodo, record, {}, "1.0.0")
    assert zenodo.calls == [("delete_file", "gone.txt")]


def test_check_record_md5_ok(tmp_path):
    path = _write_file(tmp_path, "one.txt", "hello")
    _check_record_md5(_v1_record(1, {"one.txt": _md5("hello")}), {"one.txt": path}, "1.0.0")


def test_check_record_md5_mismatch(tmp_path):
    path = _write_file(tmp_path, "one.txt", "hello")
    with pytest.raises(ZenodoError):
        _check_record_md5(_v1_record(1, {"one.txt": _md5("bye")}), {"one.txt": path}, "1.0.0")


def test_check_record_md5_missing_locally(tmp_path):
    with pytest.raises(ZenodoError):
        _check_record_md5(_v1_record(1, {"gone.txt": _md5("hello")}), {}, "1.0.0")


def test_check_record_md5_missing_online(tmp_path):
    path = _write_file(tmp_path, "one.txt", "hello")
    with pytest.raises(ZenodoError):
        _check_record_md5(_v1_record(1, {}), {"one.txt": path}, "1.0.0")


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
    _refresh_existing_record(zenodo, 7, config, [])
    assert zenodo.calls == [
        ("get_record", 7),
        ("get_versions", 7),
        ("edit_record", 7),
        ("update_metadata", 7, PUBLICATION_DATE),
        ("publish_record", 7),
    ]


@pytest.mark.parametrize("version", ["1.1.0", "0.9.0", "2024-06-01", "second-release"])
def test_refresh_existing_record_published_unpublished_version(tmp_path, version):
    """Any local version that was never published becomes a new version on Zenodo."""
    config = _config_with_version(tmp_path, version)
    zenodo = _FakeZenodo(_published(7, "1.0.0"))
    _refresh_existing_record(zenodo, 7, config, [])
    assert ("create_new_version", 7) in zenodo.calls
    # A new version is published on the day it is created, not on the day the parent was.
    assert ("update_metadata", 7, None) in zenodo.calls
    assert config.path_record_id.read_text().strip() == "7"


def test_refresh_existing_record_published_version_taken(tmp_path):
    """A local version that is already published as an older version is refused."""
    config = _config_with_version(tmp_path, "1.0.0")
    versions = [_published(7, "1.0.0", is_latest=False), _published(8, "1.1.0")]
    zenodo = _FakeZenodo(versions[1], versions)
    with pytest.raises(ZenodoError) as exc_info:
        _refresh_existing_record(zenodo, 8, config, [])
    assert "already published as record 7" in str(exc_info.value)


def test_refresh_existing_record_published_stale_record_id(tmp_path):
    """A record id pointing to an older version is refused, even at a matching version."""
    config = _config_with_version(tmp_path, "1.0.0")
    versions = [_published(7, "1.0.0", is_latest=False), _published(8, "1.1.0")]
    zenodo = _FakeZenodo(versions[0], versions)
    with pytest.raises(ZenodoError) as exc_info:
        _refresh_existing_record(zenodo, 7, config, [])
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
    """A draft has no `is_published` flag and its metadata is updated in place."""
    path = _write_file(tmp_path, "one.txt", "hello")
    config = _config_with_version(tmp_path, "1.0.0")
    record = _v1_record(7, {}, metadata={"version": "1.0.0"})
    zenodo = _FakeZenodo(record)
    _refresh_existing_record(zenodo, 7, config, [path])
    assert zenodo.calls == [
        ("get_record", 7),
        ("start_uploads", ["one.txt"]),
        ("upload_file", "one.txt"),
        ("update_metadata", 7, None),
    ]


def test_clean_online_deletes_drafts_on_every_page(tmp_path):
    """`--clean` removes the drafts that Zenodo serves beyond the first page."""
    config = _config_with_version(tmp_path, "1.0.0")
    config.path_record_id.write_text("7\n")
    hits = [{"id": rid, "is_published": rid % 2 == 0} for rid in range(2 * SEARCH_PAGE_SIZE + 1)]
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest(hits)
    _clean_online(zenodo, config)
    assert zenodo.rest.deleted == [
        f"records/{hit['id']}/draft" for hit in hits if not hit["is_published"]
    ]
    assert not config.path_record_id.exists()


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


def test_metadata_publication_date_today():
    """A record that is not published yet gets today's date, the only sensible guess."""
    metadata = _metadata(license=["mit"], resource_type="dataset")
    today = datetime.date.today().isoformat()
    assert metadata.to_zenodo()["publication_date"] == today
    assert metadata.to_zenodo(None)["publication_date"] == today


def test_metadata_publication_date_given():
    """The publication date of a published record is sent back unchanged."""
    metadata = _metadata(license=["mit"], resource_type="dataset")
    payload = metadata.to_zenodo(PUBLICATION_DATE)
    assert payload["publication_date"] == PUBLICATION_DATE


def test_refresh_existing_record_published_without_publication_date(tmp_path):
    """A published record that carries no date is dated today, instead of failing."""
    config = _config_with_version(tmp_path, "1.0.0")
    record = _published(7, "1.0.0")
    del record["metadata"]["publication_date"]
    zenodo = _FakeZenodo(record)
    _refresh_existing_record(zenodo, 7, config, [])
    assert ("update_metadata", 7, None) in zenodo.calls


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
    _refresh_existing_record(zenodo, 7, config, [])
    assert ("create_new_version", 7) in zenodo.calls


def test_check_version_chain_stale_record_without_version(tmp_path):
    """A version chain holding a record without a version is described without a KeyError."""
    config = _config_with_version(tmp_path, "1.0.0")
    versions = [_published_without_version(7, is_latest=False), _published_without_version(8)]
    zenodo = _FakeZenodo(versions[0], versions)
    with pytest.raises(ZenodoError) as exc_info:
        _refresh_existing_record(zenodo, 7, config, [])
    assert "Record 7 (no version)" in str(exc_info.value)
    assert "record 8 (no version)" in str(exc_info.value)


def test_start_uploads_declares_every_file(tmp_path):
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest([])
    paths = [_write_file(tmp_path, "one.txt", "hello"), _write_file(tmp_path, "two.txt", "bye")]
    zenodo.start_uploads(7, paths)
    assert zenodo.rest.posted == [
        ("records/7/draft/files", [{"key": "one.txt"}, {"key": "two.txt"}])
    ]


def test_start_uploads_without_files():
    """Zenodo rejects a request that declares no files, so a record without files sends none."""
    zenodo = ZenodoWrapper("token")
    zenodo.rest = _FakeRest([])
    zenodo.start_uploads(7, [])
    assert zenodo.rest.posted == []


def test_create_new_record_with_files(tmp_path):
    """A new record with files creates the record, uploads files, and updates metadata."""
    path = _write_file(tmp_path, "one.txt", "hello")
    config = _config_with_version(tmp_path, "1.0.0")
    zenodo = _FakeZenodo(_v1_record(7, {}))
    _upload_new_record(zenodo, config, [path])
    assert zenodo.calls == [
        ("create_new_record",),
        ("start_uploads", ["one.txt"]),
        ("upload_file", "one.txt"),
        ("update_metadata", 7, None),
    ]


def test_create_new_record_without_files(tmp_path):
    """A new record without files creates the record without starting uploads or extra updates."""
    config = _config_with_version(tmp_path, "1.0.0")
    zenodo = _FakeZenodo(_v1_record(7, {}))
    _upload_new_record(zenodo, config, [])
    assert zenodo.calls == [
        ("create_new_record",),
    ]


def test_refresh_existing_record_published_new_version_with_files(tmp_path):
    """A new version created from a published record updates metadata after refreshing files."""
    path = _write_file(tmp_path, "two.txt", "world")
    config = _config_with_version(tmp_path, "1.1.0")
    zenodo = _FakeZenodo(_published(7, "1.0.0"))
    _refresh_existing_record(zenodo, 7, config, [path])
    assert zenodo.calls == [
        ("get_record", 7),
        ("get_versions", 7),
        ("create_new_version", 7),
        ("start_uploads", ["two.txt"]),
        ("upload_file", "two.txt"),
        ("update_metadata", 7, None),
    ]
