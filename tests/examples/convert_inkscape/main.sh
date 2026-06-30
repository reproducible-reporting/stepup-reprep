#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv final.pdf final1.pdf
mv glasses.png glasses1.png
stepup watch-delete final.pdf
stepup watch-delete glasses.png
stepup run
stepup join
srr-make-inventory -o reproducibility_png_inventory.txt glasses.png glasses1.png
srr-make-inventory -o reproducibility_pdf_inventory.txt final.pdf final1.pdf

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f smile.svg ]] || exit 1
[[ -f final.pdf ]] || exit 1
[[ -f final1.pdf ]] || exit 1
[[ -f reproducibility_pdf_inventory.txt ]] || exit 1
[[ -f reproducibility_png_inventory.txt ]] || exit 1
