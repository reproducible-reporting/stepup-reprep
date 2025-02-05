# Working on a Project

## The `stepup` Program and `plan.py`

We strongly recommend that you follow the [StepUp Core "Getting Started" tutorials](https://reproducible-reporting.github.io/stepup-core/getting_started/introduction/),
to familiarize yourself with the `stepup` program.
This is the build tool that orchestrates the processing of results and the compilation of the paper.
These tutorials will give you a good understanding of how StepUp works and how to use it.

Now that you have gained a basic understanding of StepUp Core,
it will become clear why a `plan.py` file is included in the template.
The off-the-shelf `plan.py` already covers quite a few use cases,
but consider it a good starting point for further development.
In addition to the functions in `stepup.core.api`,
StepUp RepRep provides more functionality geared towards scientific publishing.
Reference documentation for these functions can be found here:

- [`stepup.reprep.api`][]
- [`stepup.reprep.tile_pdf`][]

## Git

Aside from making small changes, working on a StepUp project can greatly benefit from basic Git skills.
If you are new to Git, start with small steps and take on bigger challenges as you gain experience.

### Recommended Git Tutorials

The following sections of [GitHub's guide to Git](https://guides.github.com/) are most relevant:

- [Understanding the GitHub flow](https://guides.github.com/introduction/flow/)
- [Hello World](https://guides.github.com/activities/hello-world/)
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [Forking projects](https://guides.github.com/activities/forking/)

More recommended visual Git resources include:

- [A Visual Git Reference](https://marklodato.github.io/visual-git-guide/index-en.html)
- [5 Git resources for visual learners](https://about.gitlab.com/blog/2022/09/14/git-resources-for-visual-learners/)
- [Learn Git Branching](https://learngitbranching.js.org/) (an online game to learn Git)

### Keep Clean

It is essential to keep the Git repository organized and understandable by your co-authors.
When in doubt, ask one of your co-authors to review before making a commit.

The project template uses  [`pre-commit`](https://pre-commit.com) to clean up trivial annoyances.
Ensure you have installed `pre-commit` and activated it on your clone of the repository.

To remove all stale files (defined in `.gitignore`), run `git clean -dfX`.
However, do not use this command until you have committed all important files,
as it may inadvertently remove work in progress.

### Managing software

It is recommended to *pin* the versions of software dependencies,
so everyone is working with a consistent software environment.

This can be done by specifying versions in the `requirements.in` or `environment.yaml` files, e.g.

```text
scipy==1.13.1
```

instead of just

```text
scipy
```

For pip-based installations, the template uses
[pip-tools](https://github.com/jazzband/pip-tools)
to derive a `requirements.txt` from `requirements.in`.
This will pin not only the versions of your direct dependencies,
but also dependencies of dependencies, etc.

If one or more dependencies need to be updated,
change their versions in `requirements.txt` and execute:

```bash
pip-compile --generate-hashes requirements.in
pip-sync
```

If someone else has changed the `requirements.in`
and updated the `requirements.txt` with `pip-compile`,
you only need to run `pip-sync` to update your local environment.
