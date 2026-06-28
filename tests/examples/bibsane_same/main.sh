#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
cp original.bib references.bib
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Wait for background processes, if any.
set +e; wait -fn $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 6 ]] || exit 1
grep 'Please check the new' .stepup/fail.log

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f references.bib ]] || exit 1
cp references.bib current_references.bib
