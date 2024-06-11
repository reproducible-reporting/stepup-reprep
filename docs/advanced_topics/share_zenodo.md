# Share results using Zenodo

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


## Configure a Zenodo dataset.

To prepare a dataset, you need to create a `zenodo.yaml` file
by filling in the following template:

```yaml
# A JSON file containing all versions of the dataset in chronological order and
# their corresponding record IDs.
# This file is updated by the `reprep-share-zenodo` script.
# You should not need to modify it unless you created or discarded new records
# manually through the Zenodo web interface.
# It is recommended to commit it to the Git history.
path_versions: .zenodo-versions.json

# If you want to test the upload without using the production Zenodo platform,
# use the sandbox instead. Remove the sandbox prefix for production uploads.
endpoint: https://sandbox.zenodo.org/api

# You (or one of your collaborators) will need to create a personal token
# and store it locally, e.g., as follows.
path_token: ~/.config/sandbox-zenodo-org-token.txt
# If the token file is not present,
# the plan.py below will validate this file without uploading.

# Provide metadata for your Zenodo record.
# (This is a subset of all supported metadata on Zenodo.)
metadata:
  title: 'A title'
  # Put the version number in quotes to prevent it from being
  # interpreted as a floating-point number. (YAML gotcha.)
  version: '1.0.0'
  # Take one of the SPDX license identifiers (lowercase).
  license: cc-by-nc-4.0
  # Select the upload type from:
  # publication, poster, presentation, dataset, image,
  # video, software, lesson, physicalobject, other.
  upload_type: dataset
  creators:
    - name: 'Last name 1, First name 1'
      affiliation: >-
        Research group,
        University,
        Street and number,
        ZIP code,
        City,
        Country
    - name: 'Last name 2, First name 2'
      affiliation: >-
        Research group,
        University,
        Street and number,
        ZIP code,
        City,
        Country
    - ...

# Used to generate the description metadata field:
path_readme: zenodo.md

# The list of files to be uploaded.
paths:
  - file1
  - sub/file2
```


Keep the following in mind as you work out the details:

- To create the token, go to the settings of your
  [Zenodo account](https://zenodo.org/account/settings/applications/tokens/new/) or
  [Zenodo Sandbox account](https://sandbox.zenodo.org/account/settings/applications/tokens/new/).
  Enable the `deposit:actions` and `deposit:write` scopes when creating a new token.
  Save the token immediately, as it cannot be retrieved later.
- The list of licenses supported by Zenodo (and their identifiers)
  can be found in [SPDX License list](https://spdx.org/licenses/).
- The `path_readme` field is optional.
  If given, the Markdown file will be converted to HTML and used as description metadata.
  Alternatively, you can add a `description` field with an HTML value to the metadata.
- Zenodo does not support subdirectories,
  so files are uploaded without reference to their parent directory.
  This also means that two files with the same name in different subdirectories
  cannot both be included.
  If you have such files or if you have a large number of files, consider uploading a ZIP archive instead of separate files.

The command `reprep-share-zenodo` will create the online dataset and print the `record_id`,
which you can then enter in the configuration file.
This way, future calls will update this record instead of creating a new dataset on Zenodo.


Once you have all the files you need, run the upload script as follows:

```bash
reprep-share-zenodo zenodo.yaml
```

You can also include this command as a step in your `plan.py` file as follows:

```python
from stepup.core.api import static
from stepup.reprep.api import share_zenodo

static("zenodo.yaml", "zenodo.md", "file1", "sub/", "sub/file2")
share_zenodo("zenodo.yaml")
```


## Try the Following

When creating a publication starting from the RepRep [Template Tutorial](../from_template/introduction.md),
one can use the [`share_zenodo()`][stepup.reprep.api.share_zenodo] function to
continuously share the latest version of a publication with co-authors.
Drafts of datasets can be shared with co-authors,
in this case to give them access to the most recent build of the publication PDFs.


## Known limitations

- Funding information cannot be included in the YAML config file yet.
  The Zenodo API documentation still needs to be written to support this feature.
  See [zenodo/zenodo#950](https://github.com/zenodo/zenodo/issues/950).
  Also, adding funding details manually does not seem to work yet,
  because not all funding organizations are included.
  For now, just add funding details to the dataset description.
- Not all Zenodo metadata fields are supported.
  We may add more in future versions of StepUp RepRep.