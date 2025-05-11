#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
export SOURCE_DATE_EPOCH="315532800"
stepup boot -w -n 1 & # > current_stdout.txt &
PID=$!

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph

# Reproducibility test
mv sub/demo.html sub/demo1.html
stepup watch-delete sub/demo.html
stepup run
stepup join
stepup make-inventory -o reproducibility_inventory.txt sub/demo.html sub/demo1.html

# Wait for background processes, if any.
set +e; wait -fn $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f sub/demo.md ]] || exit 1
[[ -f sub/demo.html ]] || exit 1
[[ -f sub/demo1.html ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
