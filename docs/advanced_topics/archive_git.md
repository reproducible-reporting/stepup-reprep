# Archive a Git Repository (of a StepUp project)

## Git Repositories Versus Long-term Archival

You may consider your online Git provider (GitHub, GitLab, ...) as an archival solution,
for example, for datasets and publication source files.
Indeed, these services have proven to be dependable over the last decade.
However, their reliability alone does not make them suitable for long-term archival:

- An online Git platform is typically provided by a single company.
  While these companies are unlikely to vanish any time soon,
  they have no legal obligation to preserve your data.
  (Of course, in practice, they do a great job at keeping their servers up and running.)

- Git repositories are editable by design.
  You can even accidentally wipe them entirely with a single `git push -f` command.
  For long-term storage, a static deposition of files is preferable.

- Online Git platforms and their Large File Storage (LFS) backends have a limited capacity.
  If you exceed your data quota, you will have to pay up or clean up.

- A Git repository primarily stores (text-based) source files,
  not the output derived from those source files.
  With StepUp, you can easily regenerate all results and PDFs from these sources,
  so storing them in Git is not strictly necessary.
  It may also be undesirable to store output files in Git due to storage and bandwidth limitations.
  As a result, output is generally not archived in a Git repository.

    This is not a problem while you are working on a publication,
    as you are constantly using StepUp (or another tool) to build the outputs.
    However, if you are taking data from an old archive,
    regenerating the output from the sources can be a challenge.
    For example, after 10 years the required software may not be readily available
    or compatible with your current operating system.
    In such a scenario, it is preferable to also include all output in the archive.

## Preparations When Using Git LFS

Git LFS makes it easier to work with large files,
but it also complicates the archiving process.
LFS improves the efficiency of Git by storing large files externally,
so that when you clone a Git repository,
you don't have to download all versions of those large files.
Instead, LFS will only download the versions of the large files that you are working on.

### Download Large Files from LFS

If you just want to download and check out the large files in the current Git commit, run:

```bash
git lfs pull
```

If you want to archive all versions of the large files,
you will need to explicitly tell LFS to download them all.
This can take a long time and consume a lot of resources, so think twice.
If you are sure you want to do this, download all files as follows:

```bash
git lfs fetch --all
```

Some large files in your working directory may still be LFS file pointers after the `fetch` command.
To replace these pointers with the actual files, run:

```bash
git lfs checkout
```

### Migrate from an LFS-enabled Git Repository

If you want to archive the entire history including the large files,
you will need to migrate your Git repository back to a normal one without LFS.
This is relevant if you want to use the `git bundle` tool discussed below,
as it is incompatible with LFS.

This migration will make your clone incompatible with the remote repository.
The migration is also not easily reversible.
So plan this step carefully,
and make sure you really want to do this before you proceed.

The migration can be performed in two steps:

1. Get some information on LFS migration before starting:

    ```bash
    git lfs migrate info --everything
    ```

1. Perform the actual migration:

    ```bash
    git lfs migrate export --everything --include="*.*"
    ```

## Archival Recipes

The subsections below show how to archive a Git repository in different ways.
Depending on your use case, you may want to combine several archiving methods.
For example, compact archives may be preserved over longer times
than larger ones.

!!! note "Note: Work in the Git root"

    All the commands below should be run from the root directory of your Git repository.
    Archives created using the instructions below will be added to this directory,
    and will need to be uploaded or moved to a long-term storage.
    (The details of the long-term storage are beyond the scope of this tutorial.)

### Archive the Source History

!!! warning "Warning: `git bundle` archives LFS pointers, not large files."

    If your repository contains Git LFS objects,
    `git bundle` will archive the file pointers instead of the large files.
    If you want to include the large files in the bundle,
    you must first migrate from an LFS-enabled repository to a normal one,
    as explained above.

The following command will archive the entire history
of the source files in the Git repository:

```bash
git bundle create main.bundle main
```

It is recommended that you use a more descriptive name than `main.bundle`.
The bundle file will contain the entire history of the `main` branch
and some metadata stored under `.git/`.
You can specify additional branches.
For more details on bundles, see the
[Git bundle documentation](https://git-scm.com/docs/git-bundle).

If you want to recreate a Git repository from a bundle, run:

```bash
git clone main.bundle
```

### Archive Source Files from the Latest Commit

There are two options, the latter of which is preferable:

1. You can create a Git bundle with a single commit,
   which is subject to the same LFS considerations mentioned above:

    ```bash
    git bundle create main.bundle -1 main
    ```

2. You can create a ZIP file containing all the source files
   using StepUp RepRep's [Inventory Files](inventory_files.md):

    - Make sure that the working tree is clean.
      The `git status` command should print
      `nothing to commit, working tree clean`.

    - Write an `inventory-main.def` file with the following line,
      to include all files recorded by Git:

        ```text
        include-git
        ```

    - Create an `inventory-main.txt` file of the entire source tree,
      using the following command in the terminal:

        ```bash
        rr-make-inventory -i inventory-main-latest.def
        ```

        This will write a complete listing to `inventory-main.txt`

    - Then create a (reproducible) ZIP file from the `.txt` file
      by running the following command:

        ```bash
        rr-zip-inventory inventory-main-latest.txt main-latest.zip
        ```

### Archiving Source and Output Files from the Last Commit

This is similar to the previous section, but now with a larger set of files.
Create an `inventory-main-latest-with-outputs.def` file
that will include all files recorded by Git and all outputs of the StepUp workflows:

```text
include-git
include-workflow BUILT */.stepup/workflow.mpk.gz
```

(It is assumed that all STATIC files are already checked into the Git repository.)
With this file, just follow the same steps as in option 2 of the previous subsection.

## Create a `README.md` for the Archives

Archives created using the instructions above must be accompanied by a `README.md`
file that includes the following:

- A brief overview of the archive files and a few sentences  about their contents.
  The archive file itself should also contain a top-level `README.md` file,
  to refer to for more details.

- An explanation of how the archives were created and how to use or unpack them.
  You can copy and paste from this documentation and modify it as needed.
