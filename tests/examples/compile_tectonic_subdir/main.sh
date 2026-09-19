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
[[ -f sub/paper.pdf ]] || exit 1
[[ -f sub/paper.dep ]] || exit 1
[[ ! -e paper.pdf ]] || exit 1
[[ ! -e sub/sub ]] || exit 1
grep smile.pdf sub/paper-inventory.txt
grep generated.tex sub/paper-inventory.txt
grep references.bib sub/paper-inventory.txt
srr-check-inventory sub/paper-inventory.txt
