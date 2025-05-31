#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
export SOURCE_DATE_EPOCH="315532800"
export PYDEVD_DISABLE_FILE_VALIDATION=1
stepup boot -w -n 1 & # > current_stdout.txt &
PID=$!

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Wait for background processes, if any.
set +e; wait -fn $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f demo_out.ipynb ]] || exit 1
[[ -f result.txt ]] || exit 1
grep "dpi: 50" result.txt
