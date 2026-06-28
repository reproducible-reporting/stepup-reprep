#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv example.png example1.png
stepup watch-delete example.png
stepup run
stepup join
srr-make-inventory -o reproducibility_inventory.txt example.png example1.png

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f example.pdf ]] || exit 1
[[ -f example.png ]] || exit 1
[[ -f example1.png ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
