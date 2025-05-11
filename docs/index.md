# Welcome to StepUp RepRep

StepUp RepRep is the publication build tool for
[Reproducible Reporting](https://github.com/reproducible-reporting).
It is a domain-specific extension of a powerful universal build tool called
[StepUp Core](https://reproducible-reporting.github.io/stepup-core/).

To get started, we recommend to follow the
[Template Tutorial](from_template/introduction.md) in this documentation.
StepUp RepRep will be installed in your instance of the template, as part of the setup.

If you want to gain a more in-depth understanding of how StepUp works,
the [StepUp Core tutorials](https://reproducible-reporting.github.io/stepup-core/getting_started/introduction/)
will take you through all the basics.

## Quick Demo

The following screen cast shows StepUp RepRep in action:

- First, StepUp is started with 4 workers
  to complete the steps in the RepRep publication template from scratch.
- After the build has completed,
  the file `generate.py` is modified,
  whose output is used in a matplotlib plot created by `plot.py`,
  whose output is included in a LaTeX document, etc.
- Stepup sees the changes.
  As soon as the user presses `r`,
  StepUp executes the necessary steps to rebuild all artifacts
  that are (indirectly) affected by the change in `generate.py`.
- Finally, the user presses `q` to exit StepUp.

<script src="https://asciinema.org/a/718835.js" id="asciicast-718835" async="true"></script>

## Why Was StepUp RepRep Created?

StepUp RepRep aims to facilitate the reproducibility and data management of scientific publications.
It targets the *last mile* of the publication process:
The creation of a publication from raw research results.

The making of a scientific publication involves many moving parts,
which are not easily connected and shared among co-authors.
Raw results need to be analyzed, tabulated, and plotted and presented in a convenient way to the reader.
Today, such data processing is increasingly done using scripting languages (Python, R, Notebooks, ...)
because they allow more advanced analysis than spreadsheets or manual calculations.
Too often, however, the results of such scripting tools are incorporated
into a publication (or subsequent analysis tool) by tedious copy-paste or manual import.
While each tool can be very advanced,
the transfer of information from one step to the next is often not.
This becomes problematic in at least the following scenarios:

1. When trying to reproduce the results of a paper, long after it was published,
   you may not remember how intermediate results were transferred between different analysis tools
   and how these results were transformed into a presentable form in the publication.
   In such situations, published results are not easily reproducible.
   (They may still be formally reproducible, given an almost infinite amount of time and coffee.)

2. If a small error in one of the analysis scripts is fixed,
   at least a part of the analysis must be repeated.
   Every step after the fixed part and all data transfers between them must also be repeated.
   Especially if such fixes occur regularly in the writing process,
   the repetitive analysis and data transfers become very error-prone,
   which undermines the quality of the publication.

3. Because at least one person needs to know how to get data into and out of an analysis tool,
   the raw data and scripts will primarily reside on that person's computer or account.
   Even if the data and scripts are archived and made available,
   the knowledge of how to reproduce these results is not easily shared.

StepUp RepRep overcomes these difficulties by fully formalizing
the interactions between different scripts, analysis tools and authoring software.
Once configured, the entire process,
from raw results and source files all the way to a ZIP file to be uploaded to the publisher,
can be reproduced by simply running the `stepup` program once.

## Git and Virtual Environments

A project produced with StepUp RepRep uses the following technologies
to further facilitate data management and reproducibility:

- The entire publication source,
  along with all analysis scripts necessary to generate final tables and figures,
  is developed in a Git repository.
  All co-authors have access to this repository,
  so they can (if they wish) verify every detail that leads to the published results.

- A virtual software environment (Pip or Conda) is configured,
  allowing all co-authors to locally install all software required to reproduce
  the entire publication from its sources.`
