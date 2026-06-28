#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv diff.tex diff1.tex
stepup watch-delete diff.tex
stepup run
stepup join
srr-make-inventory -o reproducibility_inventory.txt diff.tex diff1.tex

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f diff.tex ]] || exit 1
[[ -f diff1.tex ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
