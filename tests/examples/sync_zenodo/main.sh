#!/usr/bin/env -S bash -x
source ../example.rc

# Without a token, srr-sync-zenodo validates the config and skips the upload.
# Clear the variable, so the example never contacts Zenodo on a developer machine.
unset REPREP_ZENODO_TOKEN

# First start: the inventory is written, and the sync warns that the token is not set.
sb -w -j 1 & # > current_stdout1.txt &
PID=$!

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Wait for background processes, if any.
set +e; wait $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f README.txt ]] || exit 1
[[ -f zenodo_description.md ]] || exit 1
[[ -f zenodo_inventory.jsonl ]] || exit 1
[[ ! -f .zenodo-record-id.txt ]] || exit 1

# Second start, with an empty token: only the sync runs, because StepUp started,
# and it warns that the token is empty.
export REPREP_ZENODO_TOKEN=
rm .stepup/*.log
sb -w -j 1 & # > current_stdout2.txt &
PID=$!

stepup wait
stepup join

set +e; wait $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1
unset REPREP_ZENODO_TOKEN
grep -q 'START.*srr-sync-zenodo' .stepup/success.log
! grep -q 'START.*srr-make-inventory' .stepup/success.log || exit 1

# Third start, offline: no step runs merely because StepUp started.
rm .stepup/*.log
sb -w -j 1 --offline & # > current_stdout3.txt &
PID=$!

stepup wait
stepup join

set +e; wait $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1
! grep -qw START .stepup/success.log || exit 1

# Fourth start, offline, after a change of the file to upload:
# the inventory is written again, and the sync says that the build is offline.
echo "It was changed after the first start." >> README.txt
rm .stepup/*.log
sb -w -j 1 --offline & # > current_stdout4.txt &
PID=$!

stepup wait
stepup join

set +e; wait $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1
grep -q 'START.*srr-make-inventory' .stepup/success.log
grep -q 'START.*srr-sync-zenodo' .stepup/success.log

# Fifth start, online: only the sync runs, and it warns that the token is not set.
rm .stepup/*.log
sb -w -j 1 & # > current_stdout5.txt &
PID=$!

stepup wait
stepup join

set +e; wait $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1
grep -q 'START.*srr-sync-zenodo' .stepup/success.log
! grep -q 'START.*srr-make-inventory' .stepup/success.log || exit 1
