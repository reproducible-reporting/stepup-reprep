#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
export SOURCE_DATE_EPOCH="315532800"
export REPREP_LATEX="xelatex"
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
rm paper.aux
sleep 0.1
rm paper.log
sleep 0.1
rm subdir/generated.tex
sleep 0.1
rm subdir/code.txt
sleep 0.1
mv paper.pdf paper1.pdf
stepup watch-delete paper.pdf
stepup watch-delete subdir/generated.tex
stepup watch-delete subdir/code.txt
stepup run
stepup join
srr-make-inventory -o reproducibility_inventory.txt paper.pdf paper1.pdf

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f paper.pdf ]] || exit 1
[[ -f paper.log ]] || exit 1
[[ -f paper.aux ]] || exit 1
[[ -f paper1.pdf ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
srr-check-inventory paper-inventory.txt
