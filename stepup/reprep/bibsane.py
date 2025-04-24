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
"""Sanitize BibTeX files."""

import argparse
import enum
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Collection

import attrs
import bibtexparser
import cattrs
import yaml
from path import Path
from pyiso4.ltwa import Abbreviate

from stepup.core.hash import compute_file_digest

__all__ = ("BibsaneConfig", "main")


@enum.unique
class DuplicatePolicy(enum.Enum):
    """The three policies for duplicate entries."""

    FAIL = "fail"
    MERGE = "merge"
    IGNORE = "ignore"


@enum.unique
class FieldPolicy(enum.Enum):
    """The two policies for bibliography fields."""

    MUST = "must"
    MAY = "may"


@attrs.define
class BibsaneConfig:
    """The configuration object controling BibSane behavior.

    Note that the settings default to the most permissive and least invasive ones.
    We recommend the opposite settings, but you have to switch knowingly in the config file.
    """

    root: Path = attrs.field()
    """The parent directory of the configuration file."""

    drop_entry_types: list[str] = attrs.field(default=attrs.Factory(list))
    """The entry types to drop from the BibTeX database."""

    normalize_doi: bool = attrs.field(default=False)
    """Set to `True` to normalize the DOIs in the entries."""

    duplicate_id: DuplicatePolicy = attrs.field(default=DuplicatePolicy.IGNORE)
    """The policy for duplicate BibTeX IDs: fail, merge or ignore."""

    duplicate_doi: DuplicatePolicy = attrs.field(default=DuplicatePolicy.IGNORE)
    """The policy for duplicate DOIs: fail, merge or ignore."""

    preambles_allowed: bool = attrs.field(default=True)
    """Set to `False` to disallow @preamble entries in the BibTeX database."""

    normalize_whitespace: bool = attrs.field(default=False)
    """Set to `True` to normalize the whitespace in the field values."""

    normalize_names: bool = attrs.field(default=False)
    """Set to `True` to normalize the author and editor names.

    (This currently broken.)
    """

    fix_page_double_hyphen: bool = attrs.field(default=False)
    """Set to `True` to fix the page ranges for which no double hyphen is used."""

    abbreviate_journals: bool = attrs.field(default=True)

    custom_abbreviations: dict[str, str] = attrs.field(factory=dict)
    """Custom journal abbreviations.

    By default, pyiso4 is used to abbreviate journal names.
    The custom abbreviations can override those provided by pyiso4.
    """

    sort: bool = attrs.field(default=False)
    """Set to `True` to sort the entries by year and first author.

    The sort key is `{year}{first author lowercase last name}`.
    """

    citation_policies: dict[str, dict[str, FieldPolicy]] = attrs.field(default=attrs.Factory(dict))
    """The field policies (must or may) for each entry type."""

    @classmethod
    def from_file(cls, fn_yaml: str):
        """Instantiate a configuration from a YAML config file."""
        if fn_yaml is None:
            config = cls(os.getcwd())
        else:
            with open(fn_yaml) as f:
                data = yaml.safe_load(f)
                data.setdefault("root", os.path.dirname(fn_yaml))
                config = cattrs.structure(data, cls)
        return config


RETURN_CODE_SUCCESS = 0
RETURN_CODE_CHANGED = 1
RETURN_CODE_BROKEN = 2

# List of citations to ignore, which are added by some LaTeX templates,
# but which are not correctly parsed by python-bibtexparser.
# Related issue: https://github.com/sciunto-org/python-bibtexparser/issues/384
IGNORED_CITATIONS = {"REVTEX41Control", "achemso-control"}


def main(argv: list[str] | None = None):
    """Main program."""
    fn_bib, fn_aux, verbose, path_out, config = parse_args(argv)
    return process_aux(fn_bib, fn_aux, verbose, path_out, config)


def parse_args(argv: list[str] | None = None) -> tuple[list[str], bool, BibsaneConfig]:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-bibsane")
    parser.add_argument("bib", help="The BibTeX file to check and clean up.")
    parser.add_argument(
        "-a",
        "--aux",
        help="The LaTeX aux file of your document. If given, unused entries will be dropped.",
    )
    parser.add_argument("-q", "--quiet", default=False, action="store_true")
    parser.add_argument("-c", "--config", help="An optional configuration file")
    parser.add_argument(
        "--out",
        help="Output path for the cleaned up BibTeX file. "
        "If not given, rr-bibsane will be overwrite the given file with the cleaned up version "
        "(if any changes were needed). "
        "This will cause StepUp to drain the scheduler so you can inspect the changes and rebuild.",
    )
    args = parser.parse_args(argv)
    config = BibsaneConfig.from_file(args.config)
    return args.bib, args.aux, not args.quiet, args.out, config


def process_aux(
    fn_bib: str, fn_aux: str | None, verbose: bool, path_out: Path | None, config: BibsaneConfig
) -> int:
    """Main program."""
    # Load the bib file.
    if verbose:
        print("📂 Loading", fn_bib)
    entries, valid_duplicates = collect_entries(fn_bib, config)
    if verbose:
        print(f"   Found {len(entries)} BibTeX entries")
    retcode = RETURN_CODE_CHANGED if valid_duplicates else RETURN_CODE_BROKEN

    # Load the aux file.
    if fn_aux is not None:
        if not fn_aux.endswith(".aux"):
            if verbose:
                print("Please, give an aux file as command-line argument, got:", fn_aux)
            return RETURN_CODE_BROKEN
        if verbose:
            print("📂 Loading", fn_aux)
        citations = parse_aux(fn_aux)
        if verbose:
            print(f"   Found {len(citations)} citations")
        citations = set(citations)
        if verbose:
            print(f"   Found {len(citations)} unique citations")
        if len(citations) == 0:
            if verbose:
                print("   ❓ Ignoring aux file because there are no citations.")
        else:
            # Drop unused and check for missing
            if verbose:
                print("🔨 Checking unused and missing citations")
            entries, bibdata_complete = drop_check_citations(
                entries, citations, config.drop_entry_types
            )
            if not bibdata_complete:
                retcode = RETURN_CODE_BROKEN
            if verbose:
                print(f"   Found {len(entries)} used BibTeX entries")

    # Clean entries
    if len(config.citation_policies) > 0:
        if verbose:
            print("🔨 Validating citation policies")
        entries, valid_fields = clean_entries(entries, config.citation_policies)
        if not valid_fields:
            retcode = RETURN_CODE_BROKEN

    # Clean up things that should never be there, not optional
    if verbose:
        print("🔨 Fixing bad practices")
    entries = fix_bad_practices(entries)

    # Check for potential problems that cannot be fixed automatically, not optional.
    if verbose:
        print("🔨 Checking for potential mistakes in BibTeX keys")
    if potential_mistakes(entries):
        retcode = RETURN_CODE_BROKEN

    # Normalize the DOIs (lowercase and remove prefix)
    if config.normalize_doi:
        if verbose:
            print("🔨 Normalizing dois")
        entries, valid_dois = normalize_doi(entries)
        if not valid_dois:
            retcode = RETURN_CODE_BROKEN

    # Remove newlines
    if config.normalize_whitespace:
        if verbose:
            print("🔨 Normalizing whitespace")
        entries = normalize_whitespace(entries)

    # Normalize author and editor names
    if config.normalize_names:
        if verbose:
            print("🔨 Normalizing author and editor names")
        entries = normalize_names(entries)

    # Fix page double hyphen
    if config.fix_page_double_hyphen:
        if verbose:
            print("🔨 Fixing double hyphen in page ranges")
        entries = fix_page_double_hyphen(entries)

    # Abbreviate journal names
    if config.abbreviate_journals:
        if verbose:
            print("🔨 Abbreviating journal names")
        entries = abbreviate_journal_iso(entries, config.custom_abbreviations)

    # Merge entries
    if config.duplicate_id == DuplicatePolicy.MERGE:
        if verbose:
            print("🔨 Merging references by BibTeX ID")
        entries, merge_conflict = merge_entries(entries, "ID")
        if merge_conflict:
            retcode = RETURN_CODE_BROKEN
        if verbose:
            print(f"   Reduced to {len(entries)} BibTeX entries by merging duplicate BibTeX IDs")
    if config.duplicate_doi == DuplicatePolicy.MERGE:
        if verbose:
            print("🔨 Merging references by DOI")
        entries, merge_conflict = merge_entries(entries, "doi")
        if merge_conflict:
            retcode = RETURN_CODE_BROKEN
        if verbose:
            print(f"   Reduced to {len(entries)} BibTeX entries by merging duplicate DOIs")

    # Sort entries
    if config.sort:
        if verbose:
            print("🔨 Sorting by Year + First author")
        entries = sort_entries(entries)

    # Overwrite if needed.
    fn_out = fn_bib if path_out is None else path_out
    retcode = write_output(entries, fn_out, retcode, verbose)
    if path_out is not None and retcode == RETURN_CODE_CHANGED:
        retcode = RETURN_CODE_SUCCESS
    return retcode


def parse_aux(fn_aux: str) -> tuple[list[str], list[str]]:
    """Parse the relevant parts of a LaTeX aux file."""
    citations = []
    with open(fn_aux) as f:
        for line in f:
            parse_aux_line("citation", line, citations)
    # Filter out bogus citations
    return [citation for citation in citations if citation not in IGNORED_CITATIONS]


def parse_aux_line(prefix: str, line: str, words: list[str]):
    """Parse a (simple) line from a LaTeX aux file."""
    if line.startswith(rf"\{prefix}{{"):
        assert line.endswith("}\n")
        assert line.count("{") == 1
        assert line.count("}") == 1
        words.extend(line[line.find("{") + 1 : -2].split(","))


def collect_entries(fn_bib: str, config: BibsaneConfig) -> tuple[list[dict[str, str]], bool]:
    """Collect entries from multiple BibTeX files."""
    # Collect stuff
    seen_ids = set()
    seen_dois = set()
    entries = []
    valid = True
    bibtex_parser = bibtexparser.bparser.BibTexParser(
        homogenize_fields=True,
        ignore_nonstandard_types=False,
    )
    with open(fn_bib) as f:
        db_in = bibtexparser.load(f, bibtex_parser)
    if len(db_in.preambles) > 0 and not config.preambles_allowed:
        print("   🤖 @preamble is not allowed")
        valid = False
    for entry in db_in.entries:
        if entry["ID"] in seen_ids and config.duplicate_id == DuplicatePolicy.FAIL:
            print(f"  ‼️ Duplicate BibTeX entry: {entry['ID']}")
            valid = False
        if "doi" in entry:
            if entry["doi"] in seen_dois and config.duplicate_doi == DuplicatePolicy.FAIL:
                print(f"‼  ️ Duplicate DOI: {entry['doi']}")
                valid = False
            seen_dois.add(entry["doi"])
        entries.append(entry)
        seen_ids.add(entry["ID"])
    return entries, valid


def drop_check_citations(
    entries: list[dict[str, str]], citations: Collection[str], drop
) -> tuple[list[dict[str, str]], bool]:
    """Drop unused citations and complain about missing ones."""
    # Check for undefined references
    defined = {entry["ID"] for entry in entries}
    valid = True
    for citation in citations:
        if citation not in defined:
            print("   💀 Missing reference:", citation)
            valid = False

    # Drop unused and irrelevant entries
    result = []
    for entry in entries:
        if entry["ID"] not in citations:
            print("     Dropping unused id:", entry["ID"])
            continue
        if entry["ENTRYTYPE"] in drop:
            print("     Dropping irrelevant entry type:", entry["ENTRYTYPE"])
            continue
        result.append(entry)

    return result, valid


def clean_entries(
    entries: list[dict[str, str]], citation_policies: dict[str, dict[str, FieldPolicy]]
) -> tuple[list[dict[str, str]], bool]:
    """Clean the irrelevant fields in each entry and complain about missing ones."""
    cleaned = []
    valid = True
    for old_entry in entries:
        eid = old_entry.pop("ID")
        etype = old_entry.pop("ENTRYTYPE")
        new_entry = {"ENTRYTYPE": etype, "ID": eid}
        if "bibsane" in old_entry:
            etype = old_entry.pop("bibsane")
            new_entry["bibsane"] = etype
        entry_policy = citation_policies.get(etype)
        if entry_policy is None:
            print(f"   🤔 {eid}: @{etype} is not configured")
            valid = False
            continue
        cleaned.append(new_entry)
        for field, policy in entry_policy.items():
            if policy == FieldPolicy.MUST:
                if field not in old_entry:
                    print(f"   🫥 {eid}: @{etype} missing field {field}")
                    valid = False
                else:
                    new_entry[field] = old_entry.pop(field)
            else:
                assert policy == FieldPolicy.MAY
                if field in old_entry:
                    new_entry[field] = old_entry.pop(field)
        if len(old_entry) > 0:
            for field in old_entry:
                print(f"   💨 {eid}: @{etype} discarding field {field}")
    return cleaned, valid


def fix_bad_practices(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Fix unwarranted use of braces."""
    result = []
    for old_record in entries:
        # Strip all braces
        new_record = {
            key: value.replace("{", "").replace("}", "") for (key, value) in old_record.items()
        }
        # Except from the author, editor, note or title
        for field in "author", "editor", "note", "title":
            if field in old_record:
                new_record[field] = old_record[field]
        result.append(new_record)
    return result


def potential_mistakes(entries: list[dict[str, str]]) -> bool:
    """Detect potential mistakes in the BibTeX entry keys."""
    id_case_map = {}
    for entry in entries:
        id_case_map.setdefault(entry["ID"].lower(), []).append(entry["ID"])

    mistakes = False
    for groups in id_case_map.values():
        if len(groups) > 1:
            print("   👻 BibTeX entry keys that only differ by case:", " ".join(groups))
            mistakes = True
    return mistakes


DOI_PROXIES = [
    "https://doi.org/",
    "http://doi.org/",
    "http://dx.doi.org/",
    "https://dx.doi.org/",
    "doi:",
]


def normalize_doi(entries: list[dict[str, str]]) -> tuple[list[dict[str, str]], bool]:
    """Normalize the DOIs in the entries."""
    result = []
    valid = True
    for entry in entries:
        doi = entry.get("doi")
        if doi is None:
            new_entry = entry
        else:
            doi = doi.lower()
            for proxy in DOI_PROXIES:
                if doi.startswith(proxy):
                    doi = doi[len(proxy) :]
                    break
            if doi.count("/") == 0 or not doi.startswith("10."):
                print("   🤕 invalid DOI:", doi)
                valid = False
            new_entry = entry | {"doi": doi}
        result.append(new_entry)
    return result, valid


def normalize_whitespace(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Normalize the whitespace inside the field values."""
    return [{key: re.sub(r"\s+", " ", value) for key, value in entry.items()} for entry in entries]


def normalize_names(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Normalize the author and editor names."""
    raise NotImplementedError("processing of names is not robust in BibtexParser 1.4.0")
    result = []
    for entry in entries:
        # Warning: bibtexparser modifies entries in place.
        # It does not hurt in this case, but it can otherwise give unexpected results.
        new_entry = entry
        for field in "author", "editor":
            if field in entry:
                splitter = getattr(bibtexparser.customization, field)
                new_entry = splitter(new_entry)
                names = entry[field]
                names = [bibtexparser.latexenc.latex_to_unicode(name) for name in names]
                names = [bibtexparser.latexenc.string_to_latex(name) for name in names]
                entry[field] = " and ".join(names)
        result.append(new_entry)
    return result


def fix_page_double_hyphen(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Fix page ranges for which no double hyphen is used."""
    return [
        # Warning: bibtexparser modifies entries in place.
        # It does not hurt in this case, but it can otherwise give unexpected results.
        bibtexparser.customization.page_double_hyphen(entry)
        for entry in entries
    ]


def abbreviate_journal_iso(
    entries: list[dict[str, str]], custom: dict[str, str]
) -> list[dict[str, str]]:
    """Replace journal names by their ISO abbreviation."""
    # Abbreviate journals
    result = []
    abbreviator = Abbreviate.create()
    for entry in entries:
        journal = entry.get("journal")
        new_entry = entry
        if journal is not None and "." not in journal:
            abbrev = custom.get(journal)
            if abbrev is None:
                abbrev = abbreviator(journal, remove_part=True)
            abbrev = custom.get(abbrev, abbrev)
            new_entry = new_entry | {"journal": abbrev}
        result.append(new_entry)
    return result


def merge_entries(entries: list[dict[str, str]], field: str) -> tuple[list[dict[str, str]], bool]:
    """Merge entries who have the same value for the given field. (case-insensitive)"""
    lookup = {}
    missing_key = []
    merge_conflict = False
    for entry in entries:
        identifier = entry.get(field)
        if identifier is None:
            print(f"   👽 Cannot merge entry without {field}:", entry["ID"])
            missing_key.append(entry)
        else:
            other = lookup.setdefault(identifier, {})
            for key, value in entry.items():
                if key not in other:
                    other[key] = value
                elif other[key] != value:
                    print(f"   😭 Same {field}={identifier}, different {key}:", value, other[key])
                    merge_conflict = True
    return list(lookup.values()) + missing_key, merge_conflict


def sort_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Sort the entries in convenient way: by year, then by author."""

    def keyfn(entry):
        # Make a fake entry to avoid in-place modification.
        entry = {"author": entry.get("author", "Aaaa Aaaa"), "year": entry.get("year", "0000")}
        first_author = bibtexparser.customization.author(entry)["author"][0].lower()
        return entry["year"] + first_author

    return sorted(entries, key=keyfn)


def write_output(entries: list[dict[str, str]], fn_out: str, retcode: int, verbose: bool) -> int:
    """Write out the fixed bibtex file, in case it has changed."""
    if retcode == RETURN_CODE_CHANGED:
        # Write out a single BibTeX database.
        db_out = bibtexparser.bibdatabase.BibDatabase()
        db_out.entries = entries
        writer = bibtexparser.bwriter.BibTexWriter()
        writer.order_entries_by = None
        with tempfile.TemporaryDirectory("rr-bibsane") as dn_tmp:
            fn_tmp = os.path.join(dn_tmp, "tmp.bib")
            with open(fn_tmp, "w") as f:
                bibtexparser.dump(db_out, f, writer)
            if os.path.isfile(fn_out):
                old_hash = compute_file_digest(fn_out)
                new_hash = compute_file_digest(fn_tmp)
                if old_hash == new_hash:
                    retcode = RETURN_CODE_SUCCESS
            if retcode == RETURN_CODE_CHANGED:
                print("💾 Please check the new or corrected file:", fn_out)
                shutil.copy(fn_tmp, fn_out)
            elif verbose:
                print("😀 No changes to", fn_out)
    else:
        print(f"💥 Broken bibliography. Not writing: {fn_out}")

    return retcode


if __name__ == "__main__":
    main(sys.argv[1:])
