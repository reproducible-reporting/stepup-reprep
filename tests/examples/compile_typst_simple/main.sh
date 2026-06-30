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
[[ -f document.typ ]] || exit 1
[[ -f out.pdf ]] || exit 1
[[ -f document-inventory.txt ]] || exit 1
grep document.typ document-inventory.txt
grep out.pdf document-inventory.txt
srr-check-inventory document-inventory.txt
