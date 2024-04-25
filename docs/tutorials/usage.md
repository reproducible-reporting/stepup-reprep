# Working on a project

## The `stepup` program and `plan.py`

We strongly recommend that you follow the ["Getting Started" tutorials of StepUp Core](https://reproducible-reporting.github.io/stepup-core/getting_started/introduction/),
to familiarize yourself with the `stepup` program.
This is the build tool that orchestrates the processing of the results and compilation of the paper.
These tutorials will give you a good understanding of how StepUp works and how to use it.

Now that you have gained a basic understanding of StepUp Core,
it will become clear why there is a file `plan.py` included in the template.
The off-the-shelf `plan.py` already covers quite a few use cases,
but consider it as a good starting point for further development.
In addition to the functions in `stepup.core.api`, StepUp RepRep provides more functionality geared towards scientific publication.
Reference documentation for these functions can be found here:

- [stepup.reprep.api][]
- [stepup.reprep.tile_pdf][]

## Git

Except for making small changes, working on a StepUp project can benefit greatly from some basic Git skills.
If you are new to Git, start with small steps and take on bigger challenges as you gain experience.

### Recommended Git tutorials

The following sections of [GitHub's guide to Git](https://guides.github.com/) are most relevant:

- [Understanding the GitHub flow](https://guides.github.com/introduction/flow/)
- [Hello World](https://guides.github.com/activities/hello-world/)
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [Forking projects](https://guides.github.com/activities/forking/)

More recommended visual Git resources include:

- [A Visual Git Reference](https://marklodato.github.io/visual-git-guide/index-en.html)
- [5 Git resources for visual learners](https://about.gitlab.com/blog/2022/09/14/git-resources-for-visual-learners/)
- [Learn Git Branching](https://learngitbranching.js.org/) (an online game to learn Git)


### Keep clean

To keep the Git repository organized and understandable by your co-authors,
it is important to avoid messing it up.
If in doubt, ask one of your co-authors to take a look before you make a commit.

The project template uses  [`pre-commit`](https://pre-commit.com) to clean up trivial annoyances, which would otherwise result in diff noise.
Make sure you have installed `pre-commit` and activated it on your clone of the repository.

To remove all stale files (defined in `.gitignore`), run `git clean -dfX`.
Do not use this command before you have committed all important files,
as it may accidentally remove work in progress.
