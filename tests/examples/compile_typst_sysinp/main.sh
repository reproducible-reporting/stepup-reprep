#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
export SOURCE_DATE_EPOCH="315532800"
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f template.typ ]] || exit 1
[[ -f alice.pdf ]] || exit 1
[[ -f bob.pdf ]] || exit 1
[[ -f charlie.pdf ]] || exit 1
