#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
export PYDEVD_DISABLE_FILE_VALIDATION=1
sb -w -j 8 & # > current_stdout.txt &
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
for i in $(seq 0 7); do
  [[ -f "out_${i}.html" ]] || exit 1
done
