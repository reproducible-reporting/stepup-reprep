<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# The `srr-sync-zenodo` Configuration File

This page documents every field of the configuration file read by `srr-sync-zenodo`
and by [`sync_zenodo()`][stepup.reprep.api.sync_zenodo].
The workflow in which this file is used is described in
[Synchronize a Zenodo Dataset With Your Local Files](../advanced_topics/sync_zenodo.md).

The fields are those of the InvenioRDM API, not those of the legacy `.zenodo.json` file.
The difference is explained in
[Legacy Deposit Versus the InvenioRDM API](../advanced_topics/sync_zenodo.md#legacy-deposit-versus-the-inveniordm-api).

## Template

To prepare a dataset, you need to create a `sync_zenodo.yaml` file
you can start from the template below.

The template covers all possible fields, but you usually only need a subset of them.
(The most important ones are marked with comments.)
The custom fields are optional and many fields have sensible defaults.
More details are given in the sections below.

```yaml
path_record_id: .zenodo-record-id.txt  # required
endpoint: https://sandbox.zenodo.org/api  # our default
metadata:
  title: 'A title'        # required
  version: '1.0.0'        # required
  resource_type: dataset  # required
  publisher: 'Zenodo'     # required
  # Add at least one creator
  creators:
    - given_name: 'First name 1'
      family_name: 'Last name 1'
      identifiers:
        orcid: '0000-0002-1825-0097'
      affiliations:
        - ror: ROR_CODE  # See https://ror.org/
        - name: >-
            Research group,
            University,
            Street and number,
            ZIP code
            City,
            Country
        - name: >-
            Consortium name,
            Some more details,
            ...
    - given_name: 'First name 2'
      family_name: 'Last name 2'
      affiliations:
        - name: >-
            Research group,
            University,
            Street and number,
            ZIP code
            City,
            Country
    - ...
  keywords:
    - keyword1
    - keyword2
  license:
    - cc-by-nc-4.0  # Zenodo's default
  copyright: 'Copyright statement'
  languages:
    - eng
    - fra
  description: >-
    A short description of the dataset, in plain text or HTML.
    Anything longer is better passed in with the --description option,
    which takes a Markdown or HTML file.
  related:
    - scheme: doi
      identifier: 10.1234/zenodo.1234567
      relation_type: cites
      resource_type: publication
    - ...
  funding:
    # Describe an award that Zenodo already knows by its id.
    - funder:
        ror: ROR_CODE  # See https://ror.org/
      award:
        id: '00k4n6c32::041117'  # See https://zenodo.org/api/awards
    # Describe any other award with free text, never in combination with an id.
    - funder:
        name: 'Full name of the funder'
      award:
        title: 'Full title of the award'
        number: 'Award number'
        identifiers:
          - identifier: 'https://example.org/award/1234'
          - scheme: doi
            identifier: '10.5281/zenodo.1234567'
          - ...
custom_fields:
  code_repository: https://github.com/example/repo2
  development_status: active
  programming_languages:
    - python
    - fortran
  rights_holder:
    - 'Name of a rights holder'
    - ...
  journal:
    title: 'Full name of the journal'
    volume: '42'
    issue: '3'
    pages: '123-145'
    issn: '0378-5955'
  meeting:
    title: 'Full name of the meeting'
    acronym: 'ACRONYM'
    dates: '1-3 June 2024'
    place: 'City, Country'
    session: 'VI'
    session_part: '1'
    url: https://example.org/meeting
    identifiers:
      - scheme: doi
        identifier: '10.1234/zenodo.1234567'
      - ...
  imprint:
    title: 'Title of the book'
    isbn: '978-3-16-148410-0'
    pages: '15-30'
    place: 'City, Country'
    edition: '2nd'
  thesis:
    university: 'Name of the university'
    department: 'Name of the department'
    type: 'PhD'
    date_submitted: '2024-06-15'
    date_defended: '2024-09-23'
access:
  record: public
  files: public
```

Any key that is not listed in this template is rejected.
Values that must be strings are not coerced,
so a version number has to be quoted, for example.
Wherever a list of strings is expected,
a single value may also be written on its own,
as in `keywords: coffee`.

## File Name and Format

The name `sync_zenodo.yaml` is only a recommendation:
`srr-sync-zenodo` uses whichever path it is given.
The name is chosen to avoid confusion with the legacy `.zenodo.json` file,
which is a different file that Zenodo reads through a different code path.
A file named `.zenodo.json` is rejected as a configuration file for this reason.

The configuration may also be written in JSON or TOML.
The parser is selected by the suffix of the file name:
`.yaml` and `.yml` for YAML, `.json` for JSON and `.toml` for TOML.
There is no option to override this choice.
All three formats carry the same fields and produce the same metadata,
but YAML is recommended because it supports comments and because it results in compact files.

## `path_record_id` *(required)*

A TXT file containing the record ID of the most recent version of the resource on Zenodo.
This file is updated by the `srr-sync-zenodo` command.
You should not need to modify its contents
unless you created or discarded new records manually through the Zenodo web interface.
It is recommended to commit this file to the Git history.
Changes to this file are not tracked by StepUp.

## `endpoint` *(optional)*

The API endpoint to interact with.
It defaults to `https://sandbox.zenodo.org/api`.
Remove the `sandbox.` prefix for production uploads.

A record ID only means something on the instance that issued it,
so start from a fresh `path_record_id` file when you switch endpoints.

## `metadata` *(required)*

A section with metadata fields to describe the dataset on Zenodo.

The publication date is not a field of this file.
A record that is not published yet is dated on the day `srr-sync-zenodo` last touched it,
and a published record keeps the date Zenodo recorded when it was published,
also when its metadata is updated afterwards.
Each new version gets its own publication date this way.

- `title` *(required)*:

    > A short description of the dataset, of at least three characters.

- `version` *(required)*:

    > The version of your current data, as a non-empty string of at most 191 characters.
    > Any convention will do, such as [semantic versioning](https://semver.org/) or a date.
    >
    > Put the version number in quotes to prevent it from being
    > interpreted as a floating-point number.
    >
    > If you have published the dataset, only metadata of the published versions
    > can be updated, but not the files.
    > If you want to upload newer files, you can change this version.
    > The `srr-sync-zenodo` command will create a new version for you on Zenodo,
    > which stays in draft mode until you manually publish it through the Zenodo web interface.
    >
    > Zenodo stores the version as free text and does not order the versions of a dataset by it,
    > so `srr-sync-zenodo` only tests it for equality with the versions published on Zenodo.
    > It refuses to reuse a version that was published before,
    > because that is usually a stale checkout or a revert instead of a new release.

- `resource_type` *(required)*:

    > The type of the deposited resource, e.g. `dataset`, `software` or `publication-article`.
    > The identifiers are taken from the `resourcetypes` vocabulary,
    > described in [Controlled Vocabularies](#controlled-vocabularies) below.

- `publisher` *(required)*:

    > The name under which the dataset is made available, e.g. `Zenodo`.
    >
    > Zenodo accepts a draft without a publisher but refuses to publish it,
    > because it needs one to register a DOI.
    > It is therefore required here, so that a missing publisher is reported
    > before the record is created instead of when you try to publish it.

- `creators` *(required)*:

    > List one or more creators of the data.
    > Zenodo rejects a record without creators.
    > Each creator is a dictionary with the following fields:

    - `family_name` *(required)*:

        > The last name(s) of a creator.
        > Zenodo requires this for every creator,
        > because `srr-sync-zenodo` deposits creators as persons rather than organizations.

    - `given_name` *(optional)*:

        > The first name(s) of a creator.

    - `identifiers` *(optional)*:

        > A dictionary with identifiers of the creator.
        > The only supported identifiers are `orcid` and `isni`.
        > Write the identifier itself, without a URL prefix,
        > e.g. `0000-0001-9288-5608` and not `https://orcid.org/0000-0001-9288-5608`.

    - `affiliations` *(optional)*:

        > The list of affiliations of the creator.
        > Each affiliation is a dictionary with either a `ror` or `name` field.

- `keywords` *(optional)*:

     > A list of keywords to describe the dataset.
     > A single keyword may be written without the list markup.
     > The InvenioRDM metadata has no keyword field,
     > so Zenodo stores these as free text subjects.

- `license` *(required)*:

    > A list of license SPDX identifiers (will be converted to lowercase).
    > A single license may be written without the list markup.
    > The identifiers are taken from the `licenses` vocabulary,
    > described in [Controlled Vocabularies](#controlled-vocabularies) below.
    >
    > When specifying multiple licenses, it is recommended to clarify in the Zenodo readme
    > how the different licenses apply to different parts of the dataset.

- `copyright` *(optional)*:

    > A copyright statement describing the ownership of the dataset.

- `languages` *(optional)*:

    > A list of ISO 639-3 language codes, e.g. `eng` for English or `fra` for French.
    > A single language may be written without the list markup.
    > Zenodo uses these codes to describe the languages in which the dataset is written.

- `description` *(optional)*:

    > A description of the dataset, in plain text or HTML.
    >
    > For anything longer than a few lines, use the
    > [`--description` option](../advanced_topics/sync_zenodo.md#synchronize-your-dataset) instead.
    > The two cannot be combined.

- `related` *(optional)*:

    > A list of related resources.
    > Each resource is a dictionary with the following fields:

    - `scheme` *(required)*:

        > The identifier scheme, e.g. `doi`, `arxiv`, `isbn`, `url` or `other`.
        > These schemes are not a vocabulary of Zenodo but a fixed list of the software it runs,
        > documented at
        > [Identifier schemes](https://inveniordm.docs.cern.ch/reference/metadata/#identifier-schemes).
        >
        > The schemes that `srr-sync-zenodo` accepts, and the validator it uses for each of them,
        > are listed in `IDENTIFIER_SCHEMES` in
        > [`sync_zenodo.py`](https://github.com/reproducible-reporting/stepup-reprep/blob/main/stepup/reprep/sync_zenodo.py).

    - `identifier` *(required)*:

        > The identifier of the resource.

    - `relation_type` *(required)*:

        > The type of relation, e.g. `cites`, `ispartof` or `isversionof`.
        > Select the relation such that the following sentence works:
        > *This record {relation_type} the related record*.
        > The identifiers are taken from the `relationtypes` vocabulary,
        > described in [Controlled Vocabularies](#controlled-vocabularies) below.

    - `resource_type` *(optional)*:

        > The type of the related resource,
        > taken from the same `resourcetypes` vocabulary as `metadata.resource_type`.

- `funding` *(optional)*:

    > A list of funding information.
    > Each funding entry is a dictionary with the following fields:

    - `funder` *(required)*:

        > A dictionary with either the ROR code of the funder or its name.
        > The ROR code can be found on [ROR.org](https://ror.org/).

    - `award` *(required)*:

        > A dictionary with the details of the award.
        > Describe the award either with an `id`,
        > or with a `title` and a `number`, of which at least one must be given.
        > It can contain the following fields:

        - `id` *(optional)*:

            > The identifier of an award that Zenodo already knows,
            > e.g. `00k4n6c32::041117`.
            > These are listed at <https://zenodo.org/api/awards>.
            > Zenodo fills in the title and the number of the award itself,
            > so neither may be given alongside an `id`.

        - `title` *(optional)*:

            > The full title of the award.

        - `number` *(optional)*:

            > The award number.

        - `identifiers` *(optional)*:

            > A list of identifiers of the award, e.g. the URL of its description.
            > Each entry is a dictionary with an `identifier`
            > and an optional `scheme` taken from the same list as in the `related` section.
            > Zenodo derives the scheme from the identifier when it is left out.

## `custom_fields` *(optional)*

A section with (a subset of) fields that Zenodo adds on top of the InvenioRDM metadata.
Each group below suits a particular kind of resource:
`code_repository`, `development_status` and `programming_languages` describe software,
`journal` and `imprint` describe a publication,
`meeting` describes a contribution to a conference,
`thesis` describes a dissertation,
and `rights_holder` applies to anything.
A group that is left out entirely, or all of whose keys are unset, is not sent to Zenodo.

- `code_repository` *(optional)*:

    > The URL of the repository in which the code is hosted.
    > Zenodo reads an `http`, `https`, `ftp` or `ftps` URL
    > whose host name carries a top level domain of at least two characters.

- `development_status` *(optional)*:

    > The development status of the software.
    > One of `abandoned`, `active`, `concept`, `inactive`,
    > `moved`, `suspended`, `unsupported` or `wip`.

- `programming_languages` *(optional)*:

    > A list of programming languages in which the software is written.
    > A single language may be written without the list markup.
    > The identifiers are lowercase and use underscores instead of spaces,
    > e.g. `python`, `jupyter_notebook` or `common_lisp`.
    > They are taken from the `code:programmingLanguages` vocabulary,
    > described in [Controlled Vocabularies](#controlled-vocabularies) below.

- `rights_holder` *(optional)*:

    > A list of parties that hold the rights to the resource.
    > A single rights holder may be written without the list markup,
    > as in `rights_holder: Ghent University`.
    >
    > Use this when the rights holder is not one of the creators,
    > for example the institution that employs them.

- `journal` *(optional)*:

    > The journal in which the resource appeared.
    > All of its keys are optional and free text,
    > except the `issn`, which Zenodo validates.

    - `title` *(optional)*:

        > The full name of the journal.

    - `volume` *(optional)*:

        > The volume in which the resource appeared, e.g. `'42'`.

    - `issue` *(optional)*:

        > The issue in which the resource appeared, e.g. `'3'`.

    - `pages` *(optional)*:

        > The pages of the resource within the issue, e.g. `'123-145'`.

    - `issn` *(optional)*:

        > The International Standard Serial Number of the journal, e.g. `'0378-5955'`.
        > Zenodo reads eight digits ending in a check digit,
        > with or without the hyphen.

    ```yaml
    custom_fields:
      journal:
        title: 'Journal of Chemical Physics'
        volume: '160'
        issue: '4'
        pages: '044109'
        issn: '0021-9606'
    ```

- `meeting` *(optional)*:

    > The meeting at which the resource was presented.
    > All of its keys are optional and free text,
    > except the `url` and the `identifiers`, which Zenodo validates.

    - `title` *(optional)*:

        > The full name of the meeting.

    - `acronym` *(optional)*:

        > The short name of the meeting, e.g. `'ICC24'`.

    - `dates` *(optional)*:

        > The dates of the meeting, e.g. `'1-3 June 2024'`.
        > Zenodo stores this as written and does not parse it.

    - `place` *(optional)*:

        > Where the meeting took place, e.g. `'Ghent, Belgium'`.

    - `session` *(optional)*:

        > The session of the meeting, e.g. `'VI'`.

    - `session_part` *(optional)*:

        > The part within the session, e.g. `'1'`.

    - `url` *(optional)*:

        > The website of the meeting.
        > Zenodo reads the same kind of URL as for `code_repository`.

    - `identifiers` *(optional)*:

        > A list of identifiers of the meeting, e.g. the DOI of its proceedings.
        > Each entry is a dictionary with an `identifier`
        > and an optional `scheme` taken from the same list as in the `related` section.
        > Zenodo derives the scheme from the identifier when it is left out.

    ```yaml
    custom_fields:
      meeting:
        title: 'International Conference on Coffee'
        acronym: 'ICC24'
        dates: '1-3 June 2024'
        place: 'Ghent, Belgium'
        url: https://example.org/icc24
        identifiers:
          - scheme: doi
            identifier: '10.5281/zenodo.1234567'
    ```

- `imprint` *(optional)*:

    > The book or report in which the resource appeared.
    > All of its keys are optional and free text,
    > except the `isbn`, which Zenodo validates.

    - `title` *(optional)*:

        > The title of the book in which the resource appeared as a chapter.

    - `isbn` *(optional)*:

        > The International Standard Book Number, e.g. `'978-3-16-148410-0'`.
        > Zenodo reads a ten or thirteen digit number ending in a check digit,
        > with or without the hyphens.

    - `pages` *(optional)*:

        > The pages of the resource within the book, e.g. `'15-30'`.

    - `place` *(optional)*:

        > The place of publication, e.g. `'Ghent, Belgium'`.

    - `edition` *(optional)*:

        > The edition of the book, e.g. `'2nd'`.

    ```yaml
    custom_fields:
      imprint:
        title: 'Handbook of Coffee'
        isbn: '978-3-16-148410-0'
        pages: '15-30'
        place: 'Ghent, Belgium'
        edition: '2nd'
    ```

- `thesis` *(optional)*:

    > The dissertation of which the resource is the outcome.
    > All of its keys are optional and free text,
    > but the two dates are partially validated, as explained below.

    - `university` *(optional)*:

        > The institution that awarded the degree.

    - `department` *(optional)*:

        > The department within that institution.

    - `type` *(optional)*:

        > The kind of thesis, e.g. `'PhD'` or `'Master'`.

    - `date_submitted` *(optional)*:

        > The date on which the thesis was submitted.

    - `date_defended` *(optional)*:

        > The date on which the thesis was defended.

    ```yaml
    custom_fields:
      thesis:
        university: 'Ghent University'
        department: 'Center for Molecular Modeling'
        type: 'PhD'
        date_submitted: '2024-06-15'
        date_defended: '2024-09-23'
    ```

    Zenodo reads both dates as an EDTF level 2 expression,
    which also covers uncertain and approximate expressions such as `1984~` or `1984-06-uu`.
    `srr-sync-zenodo` does not reimplement that grammar.
    It only checks a value that looks like a plain calendar date,
    i.e. `YYYY`, `YYYY-MM` or `YYYY-MM-DD`,
    which rejects a mistake such as `2024-13-01` before the deposit is attempted.
    Any other value is passed on to Zenodo, which has the final say.

There is deliberately no `creator` custom field,
even though Zenodo deploys one under the name `dc:creator`.
It holds names as free text, without ORCIDs or affiliations,
so it can only repeat what `metadata.creators` already records in a structured form.
List the authors in `metadata.creators` and nowhere else.

## `access` *(optional)*

Who can see the record and who can download its files.
Both keys are optional and default to `public`.

- `record` *(optional)*:

    > Either `public` or `restricted`.
    > The metadata of the record and its landing page are visible to everyone
    > when this is `public`,
    > and only to you and the people you share the record with when it is `restricted`.

- `files` *(optional)*:

    > Either `public` or `restricted`.
    > The files can be downloaded by everyone when this is `public`.

A restricted record can be shared with others through the sharing links of Zenodo.
These are created in the Zenodo web interface and are outside the scope of `srr-sync-zenodo`.
Embargoes, which make a record public on a future date,
cannot be set through the configuration file.

## Controlled Vocabularies

The following table shows which fields take an identifier from a controlled vocabulary of Zenodo:

| Field | Vocabulary |
| --- | --- |
| `metadata.license` | `licenses` |
| `metadata.resource_type` | `resourcetypes` |
| `metadata.related[].resource_type` | `resourcetypes` |
| `metadata.related[].relation_type` | `relationtypes` |
| `custom_fields.development_status` | `code:developmentStatus` |
| `custom_fields.programming_languages` | `code:programmingLanguages` |

Zenodo rejects a deposit with an identifier that is not in its vocabularies,
including one that only differs in capitalization,
which is why `srr-sync-zenodo` validates these identifiers before contacting Zenodo.

StepUp RepRep documents a local copy of [Zenodo Vocabularies](zenodo_vocabularies.md)
relevant for the `srr-sync-zenodo` script,
and they are also stored in machine-readable form in
[`zenodo_vocabularies.yaml`](https://github.com/reproducible-reporting/stepup-reprep/blob/main/stepup/reprep/zenodo_vocabularies.yaml).

Note that Zenodo extends its vocabularies over time,
so an identifier that Zenodo has added since the data file was written is rejected locally.
The error message names the vocabulary URL,
so you can check there whether the identifier is valid
and, if it is, ask for a refresh of the data file.

Maintainers of `stepup-reprep` refresh the file from the Zenodo API with:

```bash
python tools/update_zenodo_vocabularies.py
```

That script rewrites `zenodo_vocabularies.yaml` and `zenodo_vocabularies.md` files in place
and prints the added and removed identifiers per vocabulary,
so that the refresh can be reviewed before it is committed.
Do not edit these files by hand.
