#!/usr/bin/env -S bash -x
source ../example.rc

# Pre-install based typst package
typst compile - /dev/null -f pdf <<< '#import "@preview/based:0.1.0": encode64'

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
[[ -f demo.typ ]] || exit 1
[[ -f random.png ]] || exit 1
[[ -f linked.svg ]] || exit 1
[[ -f embedded.svg ]] || exit 1
[[ -f demo.pdf ]] || exit 1
[[ -f demo.deps.json ]] || exit 1
grep linked.svg demo.deps.json
grep embedded.svg demo.deps.json
grep random.png demo.deps.json
