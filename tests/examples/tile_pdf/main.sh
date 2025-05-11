#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
export SOURCE_DATE_EPOCH="315532800"
export PUBLIC="public/"
stepup boot -w -n 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv figure.pdf figure1.pdf
stepup watch-delete figure.pdf
stepup run
stepup join
stepup make-inventory -o reproducibility_inventory.txt figure.pdf figure1.pdf

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f triangle.svg ]] || exit 1
[[ -f square.svg ]] || exit 1
[[ -f pentagon.svg ]] || exit 1
[[ -f hexagon.svg ]] || exit 1
[[ -f vertical.svg ]] || exit 1
[[ -f horizontal.svg ]] || exit 1
[[ -f triangle.pdf ]] || exit 1
[[ -f square.pdf ]] || exit 1
[[ -f pentagon.pdf ]] || exit 1
[[ -f hexagon.pdf ]] || exit 1
[[ -f vertical.pdf ]] || exit 1
[[ -f horizontal.pdf ]] || exit 1
[[ -f figure.pdf ]] || exit 1
[[ -f figure1.pdf ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
