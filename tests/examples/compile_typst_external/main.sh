#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
export REPREP_TYPST_INVENTORY="1"
cd stepup
export STEPUP_PATH_FILTER="+../doc:"
sb -w -j 1 & # > ../current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph ../current_graph
stepup join

# Wait for background processes, if any.
set +e; wait -fn $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f ../doc/main.pdf ]] || exit 1
grep ' other.typ$' ../doc/main-inventory.txt
grep ' generated.typ$' ../doc/main-inventory.txt
