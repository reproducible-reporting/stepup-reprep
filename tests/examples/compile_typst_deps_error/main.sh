#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
echo "broken: old" > data.yaml
export REPREP_KEEP_TYPST_DEPS="1"
sb -w -j 1 & # > current_stdout.txt &
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
[[ -f document.pdf ]] || exit 1
[[ -f document.deps.json ]] || exit 1
grep data.yaml document.deps.json
[[ -f data.yaml ]] || exit 1
