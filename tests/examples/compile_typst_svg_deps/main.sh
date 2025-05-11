#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Pre-install based typst package
typst compile - /dev/null -f pdf <<< '#import "@preview/based:0.1.0": encode64'

# Run the example
export SOURCE_DATE_EPOCH="315532800"
stepup boot -w -n 1 & # > current_stdout.txt &

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
[[ -f demo.dep ]] || exit 1
grep linked.svg demo.dep
grep embedded.svg demo.dep
grep random.png demo.dep
