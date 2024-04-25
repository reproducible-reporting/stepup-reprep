# Welcome to StepUp RepRep

StepUp RepRep is the publication build tool for [Reproducible Reporting](https://github.com/reproducible-reporting).
It is a domain-specific extension of a powerful universal build tool called [StepUp Core](https://reproducible-reporting.github.io/stepup-core/).

To get started, follow the tutorials in this documentation:

- [Before you begin](tutorials/before_you_begin.md)
- [Create or clone a project](tutorials/initialize_project.md)
- [Working on a project](tutorials/usage.md)

StepUp RepRep will be installed in your instance of the template, as part of the setup.

If you want to get a more in-depth understanding of how StepUp works, the [tutorials of StepUp Core](https://reproducible-reporting.github.io/stepup-core/getting_started/introduction/) will take you through all the basics.


## Why was StepUp RepRep created?

The goal of StepUp RepRep is to facilitate the reproducibility and data management of scientific publications.
It is targeting the *last mile* of the publication process:
the creation of a publication from the raw research results.

The making of a scientific publication involves many moving parts, which are not easily connected and shared among co-authors.
Raw results must be analyzed, tabulated, and plotted to present them in a convenient form for the reader.
Today, such data processing is increasingly done using scripting languages (Python, R, Notebooks, ...) because they enable a more advanced analysis than spreadsheets or manual calculations.
Too often, however, results from such scripting tools are incorporated into a publication (or a subsequent analysis tool) by tedious copy paste or manual import.
While each tool can be very advanced, the transfer of information from one step to the next is often not.
This becomes problematic in at least the following scenarios:

1. When trying to reproduce the results of a paper (a long time after it was published),
   you may not remember how to transfer of intermediate results
   between different analysis tools and how these results were transformed into a presentable form in the publication.
   In such situations, published results are not easily reproducible.
   (They may still be formally reproducible, given an almost infinite amount of time and coffee.)
2. If a (small) error in one of the analysis scripts is fixed,
   you need to repeat at least a part of the analysis.
   Every step after the fixed part and all data transfers between them must also be repeated.
   Especially if such fixes occur regularly in the writing process,
   the repetitive analysis and data transfers becomes very error-prone,
   which undermines the quality of the publication.
3. Because (at least) one person needs to know how to get data into and out of an analysis tool, the raw data and scripts primarily exist on the computer or account of that person.
   Even if the data and scripts are archived and made available, the knowledge of how to reproduce these outcomes is not easily shared.

StepUp RepRep overcomes these difficulties by fully formalizing how different scripting and analysis tools interact.
Once configured, the entire process, from raw results and source files all the way to a ZIP file to be uploaded to the publisher, can be reproduced by simply running the `stepup` program once.


## Git and virtual environments

A project created with StepUp RepRep makes use of the following technologies to further facilitate data management and reproducibility:

- The entire publication source, with all analysis scripts to get to the final tables and figures,
  is developed in a Git repository.
  All co-authors have access to this repository, so they can (if desired) verify every little detail that leads to the published results.

- A virtual software environment (Pip or Conda) is configured, so all co-authors can locally install all the software needed to reproduce the entire publication from its sources.
