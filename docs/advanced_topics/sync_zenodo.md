---
description: >-
  Create a Zenodo draft dataset with sync_zenodo()
  and keep its metadata and files in sync with your StepUp project.
---

<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Synchronize a Zenodo Dataset With Your Local Files

!!! note "Version history"

    This feature was added to StepUp RepRep 1.3.

    As of StepUp RepRep 3.1, the schema of the configuration file has changed,
    because `sync_zenodo()` interacts with Zenodo through the InvenioRDM REST API.
    The fields that motivated the change are listed in
    [Fields Only the InvenioRDM API Offers](#fields-only-the-inveniordm-api-offers).

    As of StepUp RepRep 4.0:

    - The token is taken directly from an environment variable, instead of reading it from a file.
    - The configuration file may also be written in JSON or TOML instead of YAML.
    - The recommended file names are `sync_zenodo.yaml` for the configuration
      and `zenodo_description.md` for the description,
      instead of `zenodo.yaml` and `zenodo.md`,
      which are easily confused with the legacy `.zenodo.json` file.
    - The `custom_fields` section describes more kinds of resources,
      with the rights holder, journal, meeting, imprint and thesis fields.
    - The `publisher` field is required,
      because Zenodo refuses to publish a record without one.
    - The files to upload and the description are arguments of `sync_zenodo()`,
      so the `path_token`, `path_readme` and `paths` fields of the configuration file
      are no longer supported.

    As of StepUp RepRep 4.2, which requires StepUp Core 4.2:

    - The synchronization runs at every start of StepUp,
      so it notices when you set or unset the token,
      and it repairs a file that was deleted or changed in the draft by hand.
      See [When the Synchronization Runs](#when-the-synchronization-runs).
    - The files to upload are listed in an [inventory](inventory_files.md),
      written by `make_inventory()` or `srr-make-inventory`,
      which `sync_zenodo()` and `srr-sync-zenodo` take instead of the files themselves.
    - The description file is a required argument of `srr-sync-zenodo` and `sync_zenodo()`,
      and the configuration file no longer has a `description` field.
    - `stepup build --offline` skips the synchronization.
    - The `endpoint` field of the configuration file is required.
      It used to default to the Zenodo Sandbox.

StepUp RepRep can create a draft dataset in Zenodo on your behalf,
and automatically update it when the local versions of your files have changed.
You can also provide metadata within your StepUp project,
which minimizes the amount of GUI interaction required in the Zenodo web interface.
This approach also makes it easier for all your collaborators
to review and contribute to the (meta)data before the dataset is published on Zenodo.

You will still need to use the Zenodo web interface to publish the dataset,
and to add it to a community for review.
If your files change, and you want to create a new version,
you must change the version in the configuration file into one that was not published before.

## Legacy Deposit Versus the InvenioRDM API

Zenodo can be told about a record in more than one way,
and the three ways below are easily confused,
because they use different names for overlapping metadata.

- **The legacy deposit metadata, `.zenodo.json`.**
  This is a file in a Git repository,
  which Zenodo reads when it archives a GitHub release through its
  [GitHub integration](https://developers.zenodo.org/#github).
  Its schema is the legacy deposit schema,
  [`legacyrecord.json`](https://github.com/zenodo/zenodo/blob/master/zenodo/modules/deposit/jsonschemas/deposits/records/legacyrecord.json).
  The loader silently drops keys it does not recognize
  and rejects values outside its controlled vocabularies.
  Zenodo publishes this schema, but it lags the loader that Zenodo runs,
  which is worth knowing before you rely on it.

- **The legacy REST API, `/api/deposit/depositions`**,
  as documented on <https://developers.zenodo.org/>.
  Earlier versions of `srr-sync-zenodo` used it.

- **The InvenioRDM API, `/api/records`**,
  which `srr-sync-zenodo` currently uses.
  Zenodo does not document it itself,
  but InvenioRDM, the software that Zenodo runs, does,
  in its [REST API reference](https://inveniordm.docs.cern.ch/reference/rest_api_index/)
  and its [metadata reference](https://inveniordm.docs.cern.ch/reference/metadata/).
  It offers fields that the legacy API cannot express,
  which is why the schema of the configuration file changed in StepUp RepRep 3.1.
  These fields are listed in the next section.

A key that works in `.zenodo.json` is not necessarily a key that works here,
and vice versa, so do not blindly copy metadata between the two.
A project may well have both:
a `.zenodo.json` for the archive of its source code,
and a `sync_zenodo.yaml` for the dataset built from it.

### Fields Only the InvenioRDM API Offers

The following features of `srr-sync-zenodo` have no legacy equivalent,
as observed on 2026-08-31 in the loader that Zenodo runs,
`zenodo_rdm.legacy.deserializers`:

- `metadata.license` and `metadata.languages` are lists,
  while the legacy loader reads a single `license` and a single `language`.
- `metadata.copyright` has no legacy counterpart.
- `metadata.creators[].affiliations` is a list,
  and an affiliation may be given by its ROR identifier,
  while the legacy `affiliation` is a single free text name.
- `metadata.creators[].identifiers` accepts `isni`,
  while the legacy loader accepts only `orcid` and `gnd`.
- `metadata.related[].scheme` states the scheme of an identifier,
  while the legacy loader detects the scheme from the value and cannot be corrected.
- `metadata.funding[]` describes a funder by name or ROR identifier,
  and an award by title, number and identifiers,
  while the legacy `grants` can only refer to an award that Zenodo already knows,
  written as `<funder DOI>::<award id>`.
- `srr-sync-zenodo` also selects the file shown in the preview,
  which the legacy API does not store.

## Configure Your Zenodo Token

The `srr-sync-zenodo` command takes your personal access token
from the `REPREP_ZENODO_TOKEN` environment variable.
This is the token itself, not the path to a file containing it.

To create the token, go to the settings of your
[Zenodo account](https://zenodo.org/account/settings/applications/tokens/new/).
Enable the `deposit:actions` and `deposit:write` scopes when creating a new token.
Save the token immediately, as it cannot be retrieved later.

For a trial run, e.g. to try out `srr-sync-zenodo`, you can use the Zenodo Sandbox instead.
It has accounts and tokens of its own,
so create the token in the settings of your
[Zenodo Sandbox account](https://sandbox.zenodo.org/account/settings/applications/tokens/new/),
and set the `endpoint` field of the configuration file to `https://sandbox.zenodo.org/api`.
The [configuration reference](../reference/sync_zenodo_config.md) explains
under `endpoint` why the sandbox is not suitable for a dataset that you intend to publish.

As observed in November 2026, Zenodo answers a token of the other instance
with the same "Permission denied." as a token without the right scopes.
When Zenodo denies access, `srr-sync-zenodo` therefore reminds you of both causes.

Because the token is a secret, it is not tracked by StepUp,
so it never ends up in the workflow graph.
Instead, the synchronization step looks at the token at every start of StepUp,
so it notices when you set or unset the token between two runs of `stepup build`.
Keep the token out of your repository, for example by exporting it from a file that Git ignores.

When `REPREP_ZENODO_TOKEN` is unset or empty,
`srr-sync-zenodo` validates the configuration file, prints a warning
and exits without contacting Zenodo.
Use the `--dry-run` option to validate the configuration offline on purpose.

The endpoint is not an environment variable but a required field of the configuration file,
so that StepUp notices when you switch between the sandbox and the production instance,
and so that the configuration file shows on which instance its record lives.

## Configure a Zenodo Dataset

The metadata of the dataset is written in a configuration file,
for which `sync_zenodo.yaml` is the recommended name.
Every field of this file is documented in
[The `srr-sync-zenodo` Configuration File](../reference/sync_zenodo_config.md),
which also holds a template to start from.

The description of the dataset is written in a separate Markdown or HTML file,
for which `zenodo_description.md` is the recommended name.
Markdown is converted to HTML before it is sent to Zenodo.
A description is required, but a single sentence will do.

## Synchronize Your Dataset

The command `srr-sync-zenodo` will create or synchronize the online dataset
and store the record ID in the file named by the `path_record_id` field.
This way, future calls will update this record instead of creating a new dataset on Zenodo.

The files to upload are listed in an [inventory](inventory_files.md),
which also holds the MD5 checksum of each file.
`srr-sync-zenodo` compares these checksums with the ones that Zenodo reports,
and uploads only the files that differ.
In a StepUp workflow, the inventory is written and kept up to date by a separate step.

### In a StepUp Workflow

Include the inventory and the synchronization in your `plan.py` file:

```python
from stepup.core.api import static
from stepup.reprep.api import make_inventory, sync_zenodo

static("sync_zenodo.yaml", "zenodo_description.md", "file1", "sub/file2")
make_inventory("file1", "sub/file2", "zenodo_inventory.jsonl")
sync_zenodo("sync_zenodo.yaml", "zenodo_description.md", "zenodo_inventory.jsonl")
```

This defines two steps:

1. `srr-make-inventory file1 sub/file2 -o zenodo_inventory.jsonl`
   writes the inventory.
   StepUp runs it again only when one of the files has changed.
2. `srr-sync-zenodo sync_zenodo.yaml zenodo_description.md
   zenodo_inventory.jsonl --no-check-md5`
   synchronizes the dataset.
   It runs at every start of StepUp, as explained in
   [When the Synchronization Runs](#when-the-synchronization-runs).

The first file of the inventory is always selected as the default preview file.
Pass that file explicitly to `make_inventory()` to put it first,
because the matches of an inventory definition are sorted.
The order of the other files has no effect on Zenodo.
As of November 2026, the Zenodo API does not store an order of the files,
and the landing page of a record lists them alphabetically.
Choose the file names accordingly when their order matters.

The paths in the inventory are relative to its parent directory,
so the inventory can be put in any directory.
The `--no-check-md5` option tells `srr-sync-zenodo` to trust the checksums in the inventory,
because StepUp keeps the inventory up to date.
A start of StepUp without local changes therefore computes no checksums.
When the inventory is not built in the same workflow, e.g. for an external dataset,
pass `check_md5=True` to `sync_zenodo()`,
so that the checksums are computed again before anything is uploaded.

### Requirements for the Inventory

`srr-sync-zenodo` accepts only an inventory that can be uploaded as it is:

- The digests must be MD5 checksums, because Zenodo reports these.
  This is the default of `make_inventory()` and `srr-make-inventory`.
- The inventory must not contain symbolic links, because Zenodo has no links.
- The inventory must list at least one file,
  because Zenodo publishes no record without files
  and does not offer metadata only records.
- The files must meet the limitations of Zenodo, see below.

An inventory that does not meet these requirements is refused before Zenodo is contacted.

### By Hand

Outside a workflow, a synchronization takes two commands:
the first one writes the inventory, and the second one synchronizes the dataset.

```bash
srr-make-inventory file1 sub/file2 -o zenodo_inventory.jsonl
srr-sync-zenodo sync_zenodo.yaml zenodo_description.md zenodo_inventory.jsonl
```

Without `--no-check-md5`, `srr-sync-zenodo` computes the checksums of the files again,
and stops before it contacts Zenodo when one of them differs from the inventory.
Run `srr-make-inventory` again after every change of the files,
or run `stepup build` in a project that uses `sync_zenodo()`.

Add the `--dry-run` option to check the configuration without contacting Zenodo.
It validates the configuration file, the description and the inventory,
prints the metadata that would be sent to Zenodo and exits.
This works with or without a token,
so it is the way to review the metadata before the first upload.
It needs the inventory as well, so it also takes two commands:

```bash
srr-make-inventory file1 sub/file2 -o zenodo_inventory.jsonl
srr-sync-zenodo sync_zenodo.yaml zenodo_description.md zenodo_inventory.jsonl --dry-run
```

### Limitations of Zenodo

Zenodo does not support subdirectories,
so files are uploaded without reference to their parent directory.
This also means that two files with the same name in different subdirectories
cannot both be included.
Zenodo also limits the number of files in a record to 100.
If you run into either limitation,
consider uploading a ZIP archive made with [`zip_inventory()`][stepup.reprep.api.zip_inventory]
instead of separate files.
Upload the inventory of the ZIP archive as well,
because `srr-check-inventory` needs it to check the unpacked files.
`srr-sync-zenodo` rejects both cases before Zenodo is contacted.

### Files to Commit

The record ID file belongs in Git.
Commit it as soon as `srr-sync-zenodo` has written it,
because a clone without it creates a second record at its first start with the token.
An inventory written by `make_inventory()` does not belong in Git,
because it is an output of the build.

## When the Synchronization Runs

The synchronization step runs once at every start of StepUp.
Within the same run of `stepup build`, e.g. in watch mode,
it runs again after every change of its inputs:
the inventory, the files it lists, the configuration file and the description.

With a token, it compares the files with the checksums that Zenodo reports,
uploads the ones that differ or are missing online,
and sends the metadata again,
because Zenodo normalizes some values, so a comparison is not worth the effort.
For example, as observed on 2026-11-21, Zenodo strips the trailing newline of the description
and prefixes arXiv identifiers with `arXiv:`.
A file that was deleted or changed in the draft through the web interface
is therefore uploaded again at the next start, also when nothing changed locally.
Without a token, the step prints a warning at every start and sends nothing.

### Working Assumptions

This behavior rests on two practices:

- **A synchronization is a deliberate act.**
  Set the token only for a build that should synchronize,
  e.g. a `stepup build` with `REPREP_ZENODO_TOKEN` set after a round of edits.
  While a draft is in progress, do this regularly,
  so that your co-authors can review a recent build and the metadata.
- **One person in a team uploads.**
  Only this person sets the token, and the others review the draft without one.
  Two clones that synchronize the same record overwrite each other's files at every start
  when their builds are not identical,
  and a new version made from one clone leaves the record ID file of the other one stale.

### Offline Builds and Failures

With a token, a build fails when Zenodo cannot be reached.
Such a build passes with `stepup build --offline` or without the token.
With `--offline`, the synchronization step does not run merely because StepUp started.
When it runs because one of its inputs changed,
it says that the build is offline and sends nothing.
The next start without `--offline` synchronizes again.
Offline builds are explained in the documentation of StepUp Core, in
[Working Offline](https://reproducible-reporting.github.io/stepup-core/advanced_topics/remote_data/#working-offline).

### Published Records

When the record ID file names a published record with the version in the configuration file,
every start with the token puts the record in edit mode,
sends the metadata and publishes the record again,
with the same metadata unless the configuration file or the description changed.
Unset the token when a published record needs no further updates.

## Inspect and Reset a Dataset

Add the `--verbose` option to print every request that `srr-sync-zenodo` sends to Zenodo
and every response it receives.
The token is never printed, so the output can be shared when reporting a problem.

To start over with a draft that was never published,
discard it in the web interface of Zenodo and remove the file named by `path_record_id`.
The next run then creates a new dataset.
To drop a new version that is not published yet,
discard it in the web interface and put the id of the latest published version
back in the file named by `path_record_id`.

## Related Work

[zenodraft](https://github.com/zenodraft/zenodraft) is a Node command line tool
that also creates and updates Zenodo drafts from metadata in a repository.
It talks to the legacy deposit API and is not tied to a build system,
whereas `srr-sync-zenodo` is a StepUp step,
so the files it uploads can be the tracked outputs of a build,
and it talks to the InvenioRDM API.

## Recommended Workflow

Set up `sync_zenodo()` early,
ideally when you start a publication from the RepRep
[Template Tutorial](../from_template/introduction.md),
instead of preparing the dataset only after the manuscript is finished.
Review the metadata with `--dry-run` and create the draft.
After every round of edits, run a build with the token to refresh the draft,
and repeat this regularly while the draft is in progress.

Share the draft with your co-authors as soon as it exists.
They then have access to a recent build of the publication PDFs,
and they can review and correct the metadata while the work is still in progress,
which avoids a rush of last-minute corrections just before publication.
