<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Synchronize a Zenodo Dataset With Your Local Files

!!! note "Version history"

    This feature was added to StepUp RepRep 1.3.

    As of StepUp RepRep 3.1, the schema of the configuration file has changed,
    because `sync_zenodo()` interacts with Zenodo through the InvenioRDM REST API,
    which offers fields that the legacy Zenodo API cannot express.

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

- **The legacy REST API, `/api/deposit/depositions`.**
  This is what <https://developers.zenodo.org/> documents.
  Earlier versions of `sync_zenodo()` used it.

- **The InvenioRDM API, `/api/records`.**
  This is what `srr-sync-zenodo` uses today.
  Zenodo does not document it itself,
  but InvenioRDM, the software that Zenodo runs, does,
  in its [REST API reference](https://inveniordm.docs.cern.ch/reference/rest_api_index/)
  and its [metadata reference](https://inveniordm.docs.cern.ch/reference/metadata/).
  It offers fields that the legacy API cannot express,
  which is why the schema of the configuration file changed in StepUp RepRep 3.1.

A key that works in `.zenodo.json` is not necessarily a key that works here,
and a key of the configuration file is not necessarily a key of `.zenodo.json`,
so do not copy metadata between the two files by hand.
A project may well have both:
a `.zenodo.json` for the archive of its source code,
and a `sync_zenodo.yaml` for the dataset built from it.

## Configure Your Zenodo Token

The `srr-sync-zenodo` command takes your personal access token
from the `REPREP_ZENODO_TOKEN` environment variable.
This is the token itself, not the path to a file containing it.

To create the token, go to the settings of your
[Zenodo account](https://zenodo.org/account/settings/applications/tokens/new/) or
[Zenodo Sandbox account](https://sandbox.zenodo.org/account/settings/applications/tokens/new/).
Enable the `deposit:actions` and `deposit:write` scopes when creating a new token.
Save the token immediately, as it cannot be retrieved later.

Because the token is a secret, it is not tracked by StepUp,
so it never ends up in the workflow graph.
Keep it out of your repository, for example by exporting it from a file that Git ignores.

When `REPREP_ZENODO_TOKEN` is unset,
`srr-sync-zenodo` validates the configuration file and exits without contacting Zenodo.
Use the `--dry-run` option to validate the configuration offline on purpose.

The endpoint is not an environment variable but a field of the configuration file,
so that StepUp notices when you switch between the sandbox and the production instance.

## Configure a Zenodo Dataset

The metadata of the dataset is written in a configuration file,
for which `sync_zenodo.yaml` is the recommended name.
Every field of this file is documented in
[The `srr-sync-zenodo` Configuration File](../reference/sync_zenodo_config.md),
which also holds a template to start from.

## Synchronize Your Dataset

The command `srr-sync-zenodo` will create or synchronize the online dataset
and store the record ID in the file named by the `path_record_id` field.
This way, future calls will update this record instead of creating a new dataset on Zenodo.

The files to be uploaded are not listed in the configuration file
but are given as arguments after the configuration file.
The `--description` option takes a Markdown or HTML file with the description of the dataset.
Once you have all the files you need, execute the script:

```bash
srr-sync-zenodo sync_zenodo.yaml file1 sub/file2 \
  --description=zenodo_description.md
```

Add the `--dry-run` option to check the configuration without contacting Zenodo.
It validates the configuration file, resolves the description,
prints the metadata that would be sent to Zenodo and exits.
This works with or without a token,
so it is the way to review the metadata before the first upload.

```bash
srr-sync-zenodo sync_zenodo.yaml file1 sub/file2 \
  --description=zenodo_description.md --dry-run
```

You can also include this command as a step in your `plan.py` file:

```python
from stepup.core.api import static
from stepup.reprep.api import sync_zenodo

static("sync_zenodo.yaml", "zenodo_description.md", "file1", "sub/file2")
sync_zenodo(
    "sync_zenodo.yaml",
    ["file1", "sub/file2"],
    path_description="zenodo_description.md",
)
```

Because the files and the description are given as arguments,
StepUp knows all inputs of this step when the plan is made.

Zenodo does not support subdirectories,
so files are uploaded without reference to their parent directory.
This also means that two files with the same name in different subdirectories
cannot both be included.
Zenodo also limits the number of files in a record to 100.
If you run into either limitation,
consider uploading a ZIP archive instead of separate files.
`srr-sync-zenodo` rejects both cases before it contacts Zenodo.

## Related Work

[zenodraft](https://github.com/zenodraft/zenodraft) is a Node command line tool
that also creates and updates Zenodo drafts from metadata in a repository.
It talks to the legacy deposit API and is not tied to a build system,
whereas `srr-sync-zenodo` is a StepUp step,
so the files it uploads are the tracked outputs of a build,
and it talks to the InvenioRDM API.

## Recommended Workflow

Set up `sync_zenodo()` early,
ideally when you start a publication from the RepRep
[Template Tutorial](../from_template/introduction.md),
instead of preparing the dataset only after the manuscript is finished.
Review the metadata with `--dry-run`, create the draft,
and let every build refresh it afterwards.

Share the draft with your co-authors as soon as it exists.
They then always have access to the most recent build of the publication PDFs,
and they can review and correct the metadata while the work is still in progress,
which avoids a rush of last-minute corrections just before publication.
