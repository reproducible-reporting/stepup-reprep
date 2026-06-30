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
[[ -f lorem.typ ]] || exit 1
[[ -f out-1-2.png ]] || exit 1
[[ -f out-2-2.png ]] || exit 1
grep out-1-2.png lorem.deps.json
grep out-2-2.png lorem.deps.json
