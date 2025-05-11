#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
stepup boot -w -n 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv rastered/smile.pdf rastered/smile1.pdf
stepup watch-delete rastered/smile.pdf
stepup run
stepup join
stepup make-inventory -o reproducibility_inventory.txt rastered/smile.pdf rastered/smile1.pdf

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f smile.pdf ]] || exit 1
[[ -f rastered/smile.pdf ]] || exit 1
[[ -f rastered/smile1.pdf ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
