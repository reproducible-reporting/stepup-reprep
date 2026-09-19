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
[[ -f out/paper.pdf ]] || exit 1
[[ ! -e sub/paper.pdf ]] || exit 1
grep '../out/paper.pdf' sub/paper-inventory.txt
srr-check-inventory sub/paper-inventory.txt
