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
import cattrs
import pybtex.database
import yaml
from path import Path
from pyiso4.ltwa import Abbreviate
from pylatexenc.latex2text import LatexNodes2Text
from pylatexenc.latexencode import RULE_REGEX, UnicodeToLatexConversionRule, UnicodeToLatexEncoder

from stepup.core.hash import compute_file_digest

__all__ = ("BibsaneConfig", "main")


L2U = LatexNodes2Text().latex_to_text
CONVERSION_RULES = [
    # Custom LaTeX representation rules
    UnicodeToLatexConversionRule(
        RULE_REGEX,
        [
            # Use -- and --- for dashes when it is reasonable.
            (re.compile("—(?![-–])"), "---"),  # noqa: RUF001
            (re.compile("–(?![-—])"), "--"),  # noqa: RUF001
        ],
    ),
    # Add the default rules
    "defaults",
]
U2L = UnicodeToLatexEncoder(conversion_rules=CONVERSION_RULES).unicode_to_latex


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
    """The configuration object controlling BibSane behavior.

    Note that the settings default to the most permissive and least invasive ones.
    We recommend the opposite settings, but you have to switch knowingly in the config file.
    """

    root: Path = attrs.field()
    """The parent directory of the configuration file."""

    duplicate_key: DuplicatePolicy = attrs.field(default=DuplicatePolicy.IGNORE)
    """The policy for duplicate BibTeX keys: fail, merge or ignore."""

    duplicate_doi: DuplicatePolicy = attrs.field(default=DuplicatePolicy.IGNORE)
    """The policy for duplicate DOIs: fail, merge or ignore."""

    drop_entry_types: list[str] = attrs.field(default=attrs.Factory(list))
    """The entry types to drop from the BibTeX database."""

    normalize_doi: bool = attrs.field(default=False)
    """Set to `True` to normalize the DOIs in the entries."""

    normalize_whitespace: bool = attrs.field(default=False)
    """Set to `True` to normalize the whitespace in the field values."""

    fix_page_double_hyphen: bool = attrs.field(default=False)
    """Set to `True` to fix the page ranges for which no double hyphen is used."""

    abbreviate_journals: bool = attrs.field(default=False)
    """Set to `True` to abbreviate journal names using ISO4."""

    custom_abbreviations: dict[str, str] = attrs.field(factory=dict)
    """Custom journal abbreviations.

    By default, pyiso4 is used to abbreviate journal names.
    The custom abbreviations can override those provided by pyiso4.
    """

    brace_title_words: bool = attrs.field(default=False)
    """Recognize words in titles that should be wrapped in braces.

    This is performed late, after encoding to LaTeX, to avoid that the braces
    are represented as `\\{` and `\\}`.
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
                if data is None:
                    data = {}
                elif not isinstance(data, dict):
                    raise ValueError(
                        f"Invalid BibSane config file: expected a mapping at top level.({fn_yaml})"
                    )
                data.setdefault("root", os.path.dirname(fn_yaml))
                config = cattrs.structure(data, cls)
        return config


RETURN_CODE_SUCCESS = 0
RETURN_CODE_CHANGED = 1
RETURN_CODE_BROKEN = 2


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)

    # Load the bib file.
    print("📂 Load", args.bib)
    entries = collect_entries(args.bib)
    print(f"    Found {len(entries)} BibTeX entries")

    # Check for duplicate keys
    # TODO: This is currently pointless because pybtex already fails early on duplicate keys.
    if args.config.duplicate_key == DuplicatePolicy.FAIL:
        print("🔨 Checking for duplicate BibTeX entry keys")
        if not check_duplicate_keys(entries):
            print("    ❌ Stop early due to duplicate BibTeX entry keys")
            return RETURN_CODE_BROKEN

    # Check for duplicate DOIs
    if args.config.duplicate_doi == DuplicatePolicy.FAIL:
        print("🔨 Checking for duplicate DOIs")
        if not check_duplicate_dois(entries):
            print("    ❌ Stop early due to duplicate DOIs")
            return RETURN_CODE_BROKEN

    # Load the aux file.
    if args.aux is not None:
        if not args.aux.endswith(".aux"):
            print("    ❌ Aux file has no extension .aux:", args.aux)
            return RETURN_CODE_BROKEN
        print("📂 Load", args.aux)
        citations = parse_aux(args.aux)
        print(f"    Found {len(citations)} citations")
        citations = set(citations)
        print(f"    Found {len(citations)} unique citations")
        if len(citations) == 0:
            print("    ❓ Ignored aux file because it lacks citations.")
        else:
            # Drop unused and check for missing
            print("🔨 Checking unused and missing citations")
            bibdata_complete = check_citations(entries, citations)
            print(f"    Found {len(entries)} used BibTeX entries")
            if not bibdata_complete:
                print("    ❌ Stop early due to missing citations")
                return RETURN_CODE_BROKEN

    # Drop irrelevant entry types
    if len(args.config.drop_entry_types) > 0:
        print("🔨 Drop irrelevant entry types")
        drop_entry_types(entries, args.config.drop_entry_types)
        print(f"    {len(entries)} BibTeX entries left")

    # The default return code, assuming some changes are made but no errors found.
    retcode = RETURN_CODE_CHANGED

    # Clean entries
    if len(args.config.citation_policies) > 0:
        print("🔨 Apply and check citation policies")
        if not clean_entries(entries, args.config.citation_policies):
            retcode = RETURN_CODE_BROKEN

    # Check for potential problems that cannot be fixed automatically, not optional.
    # TODO: This is currently pointless because pybtex already fails early on duplicate keys.
    print("🔨 Check for potential mistakes in BibTeX keys")
    if not case_consistent_keys(entries):
        retcode = RETURN_CODE_BROKEN

    # Normalize the DOIs (lowercase and remove prefix)
    if args.config.normalize_doi:
        print("🔨 Normalize DOIs")
        valid_dois = normalize_doi(entries)
        if not valid_dois:
            retcode = RETURN_CODE_BROKEN

    # Remove redundant whitespace
    # TODO: This is mostly redundant because pybtex already normalizes whitespace.
    if args.config.normalize_whitespace:
        print("🔨 Normalize whitespace")
        normalize_whitespace(entries)

    # Fix page double hyphen
    if args.config.fix_page_double_hyphen:
        print("🔨 Fix double hyphen in page ranges")
        if not fix_page_double_hyphen(entries):
            retcode = RETURN_CODE_BROKEN

    # Abbreviate journal names
    if args.config.abbreviate_journals:
        print("🔨 Abbreviate journal names")
        abbreviate_journal_iso(entries, args.config.custom_abbreviations)

    # Merge entries
    if args.config.duplicate_key == DuplicatePolicy.MERGE:
        # TODO: This is currently pointless because pybtex already fails early on duplicate keys.
        print("🔨 Merge references by BibTeX key")
        if merge_entries(entries, KEY):
            retcode = RETURN_CODE_BROKEN
        print(f"    {len(entries)} entries left")
    if args.config.duplicate_doi == DuplicatePolicy.MERGE:
        print("🔨 Merge references by DOI")
        if merge_entries(entries, "doi"):
            retcode = RETURN_CODE_BROKEN
        print(f"    {len(entries)} entries left")

    # Sort entries
    if args.config.sort:
        print("🔨 Sort by Year + Author + Title")
        sort_entries(entries)

    # Overwrite if needed.
    fn_out = args.bib if args.out is None else args.out
    retcode = write_output(entries, fn_out, args.config.brace_title_words, retcode)
    if args.out is not None and retcode == RETURN_CODE_CHANGED:
        retcode = RETURN_CODE_SUCCESS
    return retcode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-bibsane",
        description="Sanitize and clean up a BibTeX file.",
    )
    parser.add_argument("bib", help="The BibTeX file to check and clean up.")
    parser.add_argument(
        "-a",
        "--aux",
        help="The LaTeX aux file of your document. If given, unused entries will be dropped.",
    )
    parser.add_argument("-c", "--config", help="An optional configuration file")
    parser.add_argument(
        "--out",
        help="Output path for the cleaned up BibTeX file. "
        "If not given, rr-bibsane will be overwrite the given file with the cleaned up version "
        "(if any changes were needed). "
        "This will cause StepUp to drain the scheduler so you can inspect the changes and rebuild.",
    )
    args = parser.parse_args(argv)
    args.config = BibsaneConfig.from_file(args.config)
    return args


class BibsaneMagicConstants(enum.Enum):
    """Magic constants for BibSane."""

    BIB_ENTRY_TYPE = enum.auto()
    BIB_KEY = enum.auto()


# Short and convenient dictionary keys for special BibTeX entry fields.
ETYPE = BibsaneMagicConstants.BIB_ENTRY_TYPE
KEY = BibsaneMagicConstants.BIB_KEY


def collect_entries(fn_bib: str) -> list[dict]:
    """Collect entries from the BibTeX files into standard Python data structures."""
    entries = []
    lib = pybtex.database.parse_file(fn_bib)
    for pyb_entry in lib.entries.values():
        # Convert to a simple dictionary, to enforce modularity between bibsane and pybtex.
        # At this stage, all keys are lowercased and LaTeX is decoded with pylatexenc
        entry = {
            ETYPE: pyb_entry.type.lower(),
            KEY: pyb_entry.key,
        }
        for key, value in pyb_entry.fields.items():
            entry[key.lower()] = L2U(value)
        for role, names in pyb_entry.persons.items():
            entry[role.lower()] = " and ".join(L2U(str(name)) for name in names)
        entries.append(entry)
    return entries


def check_duplicate_keys(entries: list[dict]) -> bool:
    """Check for duplicate BibTeX entry keys."""
    seen_ids = set()
    valid = True
    for entry in entries:
        if entry[KEY] in seen_ids:
            print(f"    ‼️ Duplicate BibTeX entry: {entry[KEY]}")
            valid = False
        seen_ids.add(entry[KEY])
    return valid


def check_duplicate_dois(entries: list[dict]) -> bool:
    """Check for duplicate DOIs."""
    seen_dois = set()
    valid = True
    for entry in entries:
        doi = entry.get("doi")
        if doi is not None:
            if doi in seen_dois:
                print(f"    ‼️ Duplicate DOI: {doi}")
                valid = False
            seen_dois.add(doi)
    return valid


# List of citations to ignore, which are added by some LaTeX templates,
# but which are not correctly parsed by python-bibtexparser.
# Related issue: https://github.com/sciunto-org/python-bibtexparser/issues/384
IGNORED_CITATIONS = {"REVTEX41Control", "achemso-control"}


def parse_aux(fn_aux: str) -> list[str]:
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
        if not (line.endswith("}\n") and line.count("{") == 1 and line.count("}") == 1):
            print("    🤕 Cannot parse aux line:", line.strip())
            return
        words.extend(line[line.find("{") + 1 : -2].split(","))


def check_citations(entries: list[dict], citations: Collection[str]) -> bool:
    """Drop unused citations and complain about missing ones."""
    # Check for undefined references
    defined = {entry[KEY] for entry in entries}
    valid = True
    for citation in citations:
        if citation not in defined:
            print("    💀 Missing reference:", citation)
            valid = False

    # Drop unused entries
    result = []
    for entry in entries:
        if entry[KEY] not in citations:
            print("    🧹 Dropping unused key:", entry[KEY])
            continue
        result.append(entry)
    entries[:] = result
    return valid


def drop_entry_types(entries: list[dict], drop: Collection[str]):
    """Drop entries of the given types."""
    result = []
    for entry in entries:
        if entry[ETYPE] in drop:
            print("    🧹 Dropping irrelevant entry type:", entry[ETYPE])
            continue
        result.append(entry)
    entries[:] = result


def clean_entries(
    entries: list[dict], citation_policies: dict[str, dict[str, FieldPolicy]]
) -> bool:
    """Clean the irrelevant fields in each entry and complain about missing ones."""
    valid = True
    for old_entry in entries:
        etype = old_entry[ETYPE]
        key = old_entry[KEY]
        new_entry = {ETYPE: etype, KEY: key}
        if "bibsane" in old_entry:
            etype = old_entry.pop("bibsane")
            new_entry["bibsane"] = etype
        entry_policy = citation_policies.get(etype)
        if entry_policy is None:
            print(f"    🤔 {key}: @{etype} is not configured")
            valid = False
            continue
        for field, policy in entry_policy.items():
            if policy == FieldPolicy.MUST:
                if field not in old_entry:
                    print(f"    🫥 {key}: @{etype} missing field {field}")
                    valid = False
                else:
                    new_entry[field] = old_entry.pop(field)
            else:
                assert policy == FieldPolicy.MAY
                if field in old_entry:
                    new_entry[field] = old_entry.pop(field)
        if len(old_entry) > 0:
            for field in old_entry:
                if field not in (ETYPE, KEY):
                    print(f"    💨 {key}: @{etype} discarding field {field}")
        old_entry.clear()
        old_entry.update(new_entry)
    return valid


def case_consistent_keys(entries: list[dict]) -> bool:
    """Detect potential mistakes in the BibTeX entry keys."""
    id_case_map = {}
    for entry in entries:
        id_case_map.setdefault(entry[KEY].lower(), []).append(entry[KEY])

    valid = True
    for groups in id_case_map.values():
        if len(groups) > 1:
            print("    👻 BibTeX entry keys that only differ by case:", " ".join(groups))
            valid = False
    return valid


DOI_PROXIES = [
    "https://doi.org/",
    "http://doi.org/",
    "http://dx.doi.org/",
    "https://dx.doi.org/",
    "doi:",
]


def normalize_doi(entries: list[dict]) -> bool:
    """Normalize the DOIs in the entries."""
    valid = True
    for entry in entries:
        doi = entry.get("doi")
        if doi is not None:
            doi = doi.lower()
            for proxy in DOI_PROXIES:
                if doi.startswith(proxy):
                    doi = doi[len(proxy) :]
                    break
            if doi.count("/") == 0 or not doi.startswith("10."):
                print("    🤕 invalid DOI:", doi)
                valid = False
            entry["doi"] = doi
    return valid


def normalize_whitespace(entries: list[dict]):
    """Normalize the whitespace inside the field values."""
    for entry in entries:
        for key, value in list(entry.items()):
            entry[key] = re.sub(r"\s+", " ", value)


HYPFUN_REGEX = "[-֊־᠆‐‑‒––―⸺⸻﹘﹣－=᐀゠⸗⹀〜〰~⸚]"  # noqa: RUF001


def fix_page_double_hyphen(entries: list[dict]) -> bool:
    """Fix page ranges for which no double hyphen is used."""
    valid = True
    for entry in entries:
        pages = entry.get("pages")
        if pages is not None:
            parts = [part.strip() for part in re.split(HYPFUN_REGEX, pages)]
            parts = [part for part in parts if part != ""]
            if len(parts) == 1:
                entry["pages"] = parts[0]
            elif len(parts) == 2:
                entry["pages"] = "--".join(parts)
            else:
                print("    🤕 invalid page range:", pages)
                valid = False
    return valid


def abbreviate_journal_iso(entries: list[dict], custom: dict[str, str]):
    """Replace journal names by their ISO abbreviation."""
    abbreviator = Abbreviate.create()
    for entry in entries:
        journal = entry.get("journal")
        if journal is not None and "." not in journal:
            abbrev = custom.get(journal)
            if abbrev is None:
                abbrev = abbreviator(journal, remove_part=False)
            print(f"    📓 {journal} -> {abbrev}")
            abbrev = custom.get(abbrev, abbrev)
            entry["journal"] = abbrev


def merge_entries(entries: list[dict], field) -> bool:
    """Merge entries who have the same value for the given key."""
    lookup = {}
    missing_field = []
    merge_conflict = False
    for entry in entries:
        identifier = entry.get(field)
        if identifier is None:
            print(f"    👽 Cannot merge entry without {field}:", entry[KEY])
            missing_field.append(entry)
        else:
            other = lookup.setdefault(identifier)
            if other is None:
                lookup[identifier] = entry
            else:
                for key, value in entry.items():
                    if key not in other:
                        other[key] = value
                    elif key != KEY and other[key] != value:
                        print(f"    😭 Same {field}={identifier}, different {key}:")
                        print(f"        {value}")
                        print(f"        {other[key]}")
                        merge_conflict = True
                print(f"    🔗 Merged entries with same {field} = {identifier}")
    result = list(lookup.values()) + missing_field
    entries[:] = result
    return merge_conflict


def sort_entries(entries: list[dict]):
    """Sort the entries in convenient way: by year, then by author."""

    def keyfn(entry):
        return (
            entry.get("year", "0000")
            + entry.get("author", "Aaaa, Aaaa")
            + entry.get("title", "Title")
        )

    entries.sort(key=keyfn)


def write_output(entries: list[dict], fn_out: str, brace_title_words: bool, retcode: int) -> int:
    """Write out the fixed bibtex file, in case it has changed.

    Parameters
    ----------
    enties
        The list of BibTeX entries as dictionaries.
    fn_out
        The output filename.
    brace_title_words
        Whether to wrap words in titles that should preserve capitalization in braces.
    retcode
        The provisional return code, based on previous checks.

    Returns
    -------
    retcode
        The final return code.
    """
    if retcode == RETURN_CODE_CHANGED:
        # Write out a single BibTeX database.
        with tempfile.TemporaryDirectory("rr-bibsane") as dn_tmp:
            fn_tmp = os.path.join(dn_tmp, "tmp.bib")

            # Convert entry dictionaries back into pybtex entries.
            lib = pybtex.database.BibliographyData()
            for entry in entries:
                pyb_entry = pybtex.database.Entry(entry[ETYPE])
                fields = [
                    (key.lower(), value) for key, value in entry.items() if key not in (ETYPE, KEY)
                ]
                fields.sort()
                for key, value in fields:
                    encoded = U2L(value)
                    if brace_title_words and key in ("title", "journal"):
                        encoded = brace_words(encoded)
                    pyb_entry.fields[key] = encoded
                lib.add_entry(entry[KEY], pyb_entry)
            lib.to_file(fn_tmp)

            # Check if the file has changed.
            if os.path.isfile(fn_out):
                old_hash = compute_file_digest(fn_out)
                new_hash = compute_file_digest(fn_tmp)
                if old_hash == new_hash:
                    retcode = RETURN_CODE_SUCCESS
            if retcode == RETURN_CODE_CHANGED:
                print("💾 Please check the new or corrected file:", fn_out)
                shutil.copy(fn_tmp, fn_out)
            else:
                print("😀 No changes to", fn_out)
    else:
        print(f"💥 Broken bibliography. Not writing: {fn_out}")

    return retcode


NEEDS_BRACES = re.compile(r"^.+[A-Z].*$")


def brace_words(title: str) -> str:
    """Wrap words in braces if it seems useful."""
    result = []
    for word in title.split():
        if NEEDS_BRACES.match(word):
            result.append(f"{{{word}}}")
        else:
            result.append(word)
    return " ".join(result)


if __name__ == "__main__":
    main(sys.argv[1:])
