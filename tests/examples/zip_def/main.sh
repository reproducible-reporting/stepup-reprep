#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Create a data directory used as static files.
mkdir -p data/sub/deeper
echo "blabla" > data/bla.inp
echo "brrrr" > data/sub/deeper/brrr.inp
echo "works" > data/sub/works.out
echo "fine" > data/fine.out
echo "nested" > data/sub/deeper/nested.out

# Run the example
stepup boot -w -n 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f inventory.txt ]] || exit 1
[[ -f upload.zip ]] || exit 1
[[ $(wc -l inventory.txt | cut -d' ' -f1) -eq 5 ]] || exit 1
