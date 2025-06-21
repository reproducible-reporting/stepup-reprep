# Upload a dataset to Zenodo

!!! note "Version history"

    This feature was added to StepUp RepRep 1.3.

StepUp RepRep can create a draft dataset in Zenodo on your behalf,
and automatically update it when the local versions of your files have changed.
You can also provide metadata within your StepUp project,
which minimizes the amount of GUI interaction required in the Zenodo web interface.
This approach also makes it easier for all your collaborators
to review and contribute to the (meta)data before the dataset is published on Zenodo.

You will still need to use the Zenodo web interface to publish the dataset.
If your files change and you want to create a new version,
you must increment the version numbers
using the [semantic version numbering](https://semver.org/) format.

## Configure a Zenodo dataset

To prepare a dataset, you need to create a `zenodo.yaml` file
by filling in the following template:

```yaml
path_versions: .zenodo-versions.json
endpoint: https://sandbox.zenodo.org/api
path_token: ~/.config/sandbox-zenodo-org-token.txt
metadata:
  title: 'A title'
  version: '1.0.0'
  license: cc-by-nc-4.0
  upload_type: dataset
  creators:
    - name: 'Last name 1, First name 1'
      affiliation: >-
        Research group,
        University,
        Street and number,
        ZIP code
        City,
        Country
      orcid: '0000-0002-1825-0097'
    - name: 'Last name 2, First name 2'
      affiliation: >-
        Research group,
        University,
        Street and number,
        ZIP code
        City,
        Country
      orcid: '0000-0002-1825-0098'
    - ...
path_readme: zenodo.md
paths:
  - file1
  - sub/file2
```

Documentation of the fields in the `zenodo.yaml` configuration file:

- `path_versions`:
  A JSON file containing all versions of the dataset in chronological order
  and their corresponding record IDs.
  This file is updated by the `stepup sync-zenodo` script.
  You should not need to modify it unless you created or discarded new records
  manually through the Zenodo web interface.
  It is recommended to commit this file to the Git history.

- `endpoint`:
  If you want to test the upload without using the production Zenodo platform,
  use the sandbox endpoint.
  Remove the `sandbox.` prefix for production uploads.

- `path_token`:
  The location of a text file with your Zenodo (sandbox) personal access token.
  If the token file is not present,
  the plan.py below will validate this file without uploading.

    To create the token, go to the settings of your
    [Zenodo account](https://zenodo.org/account/settings/applications/tokens/new/) or
    [Zenodo Sandbox account](https://sandbox.zenodo.org/account/settings/applications/tokens/new/).
    Enable the `deposit:actions` and `deposit:write` scopes when creating a new token.
    Save the token immediately, as it cannot be retrieved later.

- `metadata`:
  A section with metadata fields to describe the dataset on Zenodo.

    - `title`:
      A short description of the dataset.
    - `version`:
      The version of your current data.

        Put the version number in quotes to prevent it from being
        interpreted as a floating-point number.
        Use [semantic version numbers](https://semver.org/).

        If you have published the dataset, only metadata of the published versions
        can be updated, but not the files.
        If you want to upload newer files, you can increment this version number.
        The `stepup sync-zenodo` script will create a new version for you on Zenodo,
        which stays in draft mode until you manually publish it through the Zenodo web interface.

    - `license`:
      Lowercase license SPDX identifier.
      The list of licenses supported by Zenodo (and their identifiers)
      can be found in [SPDX License list](https://spdx.org/licenses/).

    - `upload_type`
      Select one of:
      `publication`, `poster`, `presentation`, `dataset`, `image`,
      `video`, `software`, `lesson`, `physicalobject`, or `other`.

    - `creators`:
      List one or more creators of the data.

        - `name`:
          The full name of a creator.
          Format this field as `Last name, First name`
        - `affiliation`
          The full address including affiliation.
        - `orcid`:
          The ORCID of the creator.
          Format this field as `0000-0002-1825-0097`.
          (This field is optional, but recommended.)

- `path_readme`:
  This field is optional.
  If given, the Markdown file will be converted to HTML and used as description metadata.
  Alternatively, you can add a `description` field with an HTML value to the metadata.

- `paths`:
  The dataset files to be uploaded.

    Zenodo does not support subdirectories,
    so files are uploaded without reference to their parent directory.
    This also means that two files with the same name in different subdirectories
    cannot both be included.
    If you have such files or if you have a large number of files,
    consider uploading a ZIP archive instead of separate files.

## Synchronize your dataset

The command `stepup sync-zenodo` will create or synchronize the online dataset
and store the `record_id` in the versions JSON file.
This way, future calls will update this record instead of creating a new dataset on Zenodo.

Once you have all the files you need, execute the script:

```bash
stepup sync-zenodo zenodo.yaml
```

You can also include this command as a step in your `plan.py` file:

```python
from stepup.core.api import static
from stepup.reprep.api import sync_zenodo

static("zenodo.yaml", "zenodo.md", "file1", "sub/", "sub/file2")
sync_zenodo("zenodo.yaml")
```

## Try the Following

When creating a publication starting from the RepRep [Template Tutorial](../from_template/introduction.md),
one can use the [`sync_zenodo()`][stepup.reprep.api.sync_zenodo] function to
continuously synchronize the latest version of a publication with co-authors.
Drafts of datasets can be shared with co-authors,
in this case to give them access to the most recent build of the publication PDFs.

## Known limitations

- Funding information cannot be included in the YAML config file yet.
  The Zenodo API documentation still needs to be written to support this feature.
  See [zenodo/zenodo#950](https://github.com/zenodo/zenodo/issues/950).
  (The corresponding documentation for the Web interface does not exist either.)
  Also, adding funding details manually does not seem to work yet,
  because not all funding organizations are included.
  For now, just add funding details to the dataset description.
- The Zenodo API does not support multiple affiliations.
  See [zenodo/zenodo#1608](https://github.com/zenodo/zenodo/issues/1608)
- Not all Zenodo metadata fields are supported.
  We may add more in future versions of StepUp RepRep.
