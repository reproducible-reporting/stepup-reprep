# Synchronize a Zenodo Dataset With Your Local Files

!!! note "Version history"

    This feature was added to StepUp RepRep 1.3.

    As of StepUp RepRep 3.1, the schema of the `zenodo.yaml` file has changed.
    The `sync_zenodo()` function interacts with Zenodo through the invenio RMD REST API,
    which is not officially documented yet,
    but it offers more features than the official Zenodo API.

StepUp RepRep can create a draft dataset in Zenodo on your behalf,
and automatically update it when the local versions of your files have changed.
You can also provide metadata within your StepUp project,
which minimizes the amount of GUI interaction required in the Zenodo web interface.
This approach also makes it easier for all your collaborators
to review and contribute to the (meta)data before the dataset is published on Zenodo.

You will still need to use the Zenodo web interface to publish the dataset,
and to add it to a community for review.
If your files change, and you want to create a new version,
you must increment the version numbers
using the [semantic version numbering](https://semver.org/) format.

## Configure a Zenodo dataset

To prepare a dataset, you need to create a `zenodo.yaml` file
by filling in the following template:

```yaml
path_record_id: .zenodo-record-id.txt
endpoint: https://sandbox.zenodo.org/api
path_token: ~/.config/sandbox-zenodo-org-token.txt
metadata:
  title: 'A title'
  version: '1.0.0'
  keywords:
    - keyword1
    - keyword2
  license:
    - cc-by-nc-4.0
  resource_type: dataset
  publisher: 'Publisher name'
  creators:
    - family_name: 'Last name 1'
      given_name: 'First name 1'
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
    - name: 'Last name 2, First name 2'
      identifiers:
        orcid: '0000-0002-1825-0098'
      affiliations:
        - name: >-
            Research group,
            University,
            Street and number,
            ZIP code
            City,
            Country
    - ...
  related:
    - scheme: doi
      identifier: 10.1234/zenodo.1234567
      relation_type: cites
      resource_type: publication
    - ...
  funding:
    - funder:
        ror: ROR_CODE  # See https://ror.org/
      award:
        title: 'Full title of the award'
        number: 'Award number'
        identifiers:
          - url: 'https://example.org/award/1234'
          - url: 'https://example.org/award/5678'
          - ...
code_repository: https://github.com/example/repo2
path_readme: zenodo.md
paths:
  - file1
  - sub/file2
```

Documentation of the fields in the `zenodo.yaml` configuration file:

- `path_record_id`:
  A TXT file containing the record ID of the most recent version of the resource on Zenodo.
  This file is updated by the `stepup sync-zenodo` script.
  You should not need to modify it unless you created or discarded new records
  manually through the Zenodo web interface.
  It is recommended to commit this file to the Git history.
  Changes to this file are not tracked by StepUp.

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

    - `keywords`:
      A list of keywords to describe the dataset.
      (Optional)

    - `publisher`:
      The name of the publisher of the dataset.
      (Optional)

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

    - `copyright`:
      A copyright statement describing the ownership of the dataset.
      (Optional)

    - `license`:
      A list of license SPDX identifier (will be converted to lowercase).
      The list of licenses supported by Zenodo (and their identifiers)
      can be found in [SPDX License list](https://spdx.org/licenses/).
      When specifying multiple licenses, it is recommended to clarify in the Zenodo readme
      how the different licenses apply to different parts of the dataset.

    - `resource_type`
      Select one of:

        - `audio`
        - `dataset`
        - `event`
        - `image`
        - `image-diagram`
        - `image-drawing`
        - `image-figure`
        - `image-other`
        - `image-photo`
        - `image-plot`
        - `lesson`
        - `model`
        - `other`
        - `physicalobject`
        - `poster`
        - `presentation`
        - `publication`
        - `publication-annotationcollection`
        - `publication-article`
        - `publication-book`
        - `publication-conferencepaper`
        - `publication-conferenceproceeding`
        - `publication-datamanagementplan`
        - `publication-datapaper`
        - `publication-deliverable`
        - `publication-dissertation`
        - `publication-journal`
        - `publication-milestone`
        - `publication-other`
        - `publication-patent`
        - `publication-peerreview`
        - `publication-preprint`
        - `publication-proposal`
        - `publication-report`
        - `publication-section`
        - `publication-softwaredocumentation`
        - `publication-standard`
        - `publication-taxonomictreatment`
        - `publication-technicalnote`
        - `publication-thesis`
        - `publication-workingpaper`
        - `software`
        - `software-computationalnotebook`
        - `video`
        - `workflow`

    - `creators`:
      List one or more creators of the data.

        - `family_name`:
          The last name(s) of a creator.
        - `given_name`:
          The first name(s) of a creator.
        - `identifiers`:
          A dictionary with identifiers of the creator.
          The only supported identifier are `orcid` and `isni`.
        - `affiliations`
          The list of affiliations of the creator.
          Each affiliation is a dictionary with either a `ror` or `name` field.

    - `related`:
      A list of related resources. (Optional)
      Each resource is a dictionary with the following fields:

        - `scheme`: The identifier scheme, can be any of the following:

            - `ark`
            - `arxiv`
            - `ads`
            - `crossreffunderid`
            - `doi`
            - `ean13`
            - `eissn`
            - `grid`
            - `handle`
            - `igsn`
            - `isbn`
            - `isni`
            - `issn`
            - `istc`
            - `lissn`
            - `lsid`
            - `pmid`
            - `purl`
            - `upc`
            - `url`
            - `urn`
            - `w3id`
            - `other`

        - `identifier`: The identifier of the resource.
        - `resource_type`:
          The type of the related resource, can be any of the values listed above for `resource_type`.
        - `relation_type`: The type of relation, which can be any of the following.
          Use this a in the following sentence: *This resource {relation_type} the related resource*.

            - `cites`
            - `compiles`
            - `continues`
            - `describes`
            - `documents`
            - `hasmetadata`
            - `haspart`
            - `hasversion`
            - `iscitedby`
            - `iscompiledby`
            - `iscontinuedby`
            - `isderivedfrom`
            - `isdescribedby`
            - `isdocumentedby`
            - `isidenticalto`
            - `ismetadatafor`
            - `isnewversionof`
            - `isobsoletedby`
            - `isoriginalformof`
            - `ispartof`
            - `ispreviousversionof`
            - `ispublishedin`
            - `isreferencedby`
            - `isrequiredby`
            - `isreviewedby`
            - `issourceof`
            - `issupplementedby`
            - `issupplementto`
            - `isvariantformof`
            - `isversionof`
            - `obsoletes`
            - `references`
            - `requires`
            - `reviews`

- `funding`:
  A list of funding information. (Optional)
  Each funding entry is a dictionary with the following fields:

    - `funder`: A dictionary with either the ROR code of the funder or its name.
      The ROR code can be found on [ROR.org](https://ror.org/).
    - `award`: A dictionary with the details of the award.
      It can contain the following fields:
        - `title`: The full title of the award.
        - `number`: The award number.
        - `identifiers`: A list of identifiers for the award, such as URLs.
          Each identifiers is a dictionary with a single key, the scheme,
          and the identifier as value.
          The same schemes as for the `related` section can be used here.

- `code_repository`
  Software resources, can specify the URL of the git repository. (Optional)

- `path_readme`:
  If given, it will be used as description metadata. (Optional)
  When the file has a `.md` extension, it will be converted to HTML.

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
