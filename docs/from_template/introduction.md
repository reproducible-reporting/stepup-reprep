# Introduction

This Template Tutorial is the quickest way to get started with StepUp RepRep.
It shows you how to start a new project from our
[templates](https://github.com/reproducible-reporting/templates) repository.
The template contains a pre-configured StepUp workflow that includes:

- A **dataset** directory for externally acquired data, used as input for your workflow.
- A **results** directory for collecting scripts that derive
  results, tables and figures from the dataset,
  which can then be included in the LaTeX documents below.
- Several **LaTeX documents** (from which you can remove the ones you don't need):
  article, supporting information, cover letter, reply letter, and presentation.
- An **upload** directory. Once the workflow has been executed,
  it will contain the files for uploading to
  a publisher, preprint server, conference website, etc.
- **Configuration** files for the tools used in the above steps.

All these components interact with each other.
For example, if you change a script that analyses some data,
subsequent steps that use the analysis as input will be updated when you run the workflow again.
This will not only update the figures and tables in your paper.
The ZIP file for the publisher will also be updated accordingly.
