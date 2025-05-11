#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
export SOURCE_DATE_EPOCH="315532800"
stepup boot -w -n 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv doc.pdf doc1.pdf
stepup watch-delete doc.pdf
stepup run
stepup join
stepup make-inventory -o reproducibility_inventory.txt doc.pdf doc1.pdf

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f doc.html ]] || exit 1
[[ -f doc.pdf ]] || exit 1
[[ -f doc1.pdf ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
