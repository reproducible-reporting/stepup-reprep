#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
sb -w -j 1 & # > current_stdout.txt &


# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv dst.pdf dst1.pdf
stepup watch-delete dst.pdf
stepup run
stepup join
srr-make-inventory -o reproducibility_inventory.txt dst.pdf dst1.pdf

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f src.pdf ]] || exit 1
[[ -f notes.pdf ]] || exit 1
[[ -f dst.pdf ]] || exit 1
[[ -f dst1.pdf ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
