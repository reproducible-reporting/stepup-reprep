#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f references.bib ]] || exit 1
[[ -f cleaned.bib ]] || exit 1
[[ -f copy.bib ]] || exit 1
cp cleaned.bib current_cleaned.bib
