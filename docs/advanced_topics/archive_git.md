# Git Repository Archival

## Git Repositories Versus Long-term Archival

You may consider your online Git provider (GitHub, GitLab, ...) as an archival solution,
e.g. for datasets and publication source files.
Indeed, these services have proven to be dependable over the last decade.
However, their reliability alone does not make them suitable for long-term archival:

- An online Git platform is typically provided by a single company.
  While these companies are unlikely to vanish any time soon,
  they have no legal obligation to preserve your data.
  (Of course, in practice, they do a great job at keeping of their servers up and running.)

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


### Downloading Large Files from LFS

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


### Migration from LFS to a Normal Git Repository.

If you want to archive the entire history including the large files,
you will need to migrate your Git repository back to a normal one without LFS.
This is relevant if you want to use the `git bundle` tool discussed below,
as it is incompatible with LFS.

This migration will make your local clone incompatible with the remote repository.
The migration is also not easily reversible.
So plan this step carefully, and make sure you really want to do this before you proceed.

The migration can be performed in two steps:

1. Get some information on LFS migration before starting:

    ```bash
    git lfs migrate info --everything
    ```

1. Perform the actual migration:

    ```bash
    git lfs migrate export --everything --include="*.*"
    ```


## How to Archive a Git repository

### Archive the Source History

### Archive source files from the latest commit

### Archive source and output files from the latest commit
