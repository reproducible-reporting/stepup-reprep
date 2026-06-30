#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
export REPREP_TYPST_KEEP_DEPS="1"
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv document.pdf document1.pdf
stepup watch-delete document.pdf
stepup run
stepup join
srr-make-inventory -o reproducibility_inventory.txt document.pdf document1.pdf

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f document.pdf ]] || exit 1
[[ -f document.deps.json ]] || exit 1
[[ -f image.jpg ]] || exit 1
[[ -f document1.pdf ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
