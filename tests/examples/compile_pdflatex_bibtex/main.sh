#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
export LATEX_MAIN="paper"
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
rm paper.aux paper.log
mv paper.pdf paper1.pdf
mv paper.bbl paper1.bbl
stepup watch-delete paper.pdf
stepup watch-delete paper.bbl
stepup run
stepup join
srr-make-inventory -o reproducibility_pdf_inventory.txt paper.pdf paper1.pdf
srr-make-inventory -o reproducibility_bbl_inventory.txt paper.bbl paper1.bbl

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f paper.pdf ]] || exit 1
[[ -f paper.log ]] || exit 1
[[ -f paper.aux ]] || exit 1
[[ -f paper.bbl ]] || exit 1
[[ -f paper1.pdf ]] || exit 1
[[ -f paper1.bbl ]] || exit 1
[[ -f reproducibility_pdf_inventory.txt ]] || exit 1
[[ -f reproducibility_bbl_inventory.txt ]] || exit 1
srr-check-inventory paper-inventory.txt
