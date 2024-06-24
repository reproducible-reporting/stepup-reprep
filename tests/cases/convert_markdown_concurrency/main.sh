#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
xargs rm -rvf < .gitignore

# Run the example
export SOURCE_DATE_EPOCH="315532800"
stepup -w 8 plan.py & # > current_stdout.txt &

# Wait for the director and get its socket.
export STEPUP_DIRECTOR_SOCKET=$(
  python -c "import stepup.core.director; print(stepup.core.director.get_socket())"
)

# Get the graph after completion of the pending steps.
python3 - << EOD
from stepup.core.interact import *
wait()
graph("current_graph")
join()
EOD

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f random_00.md ]] || exit 1
[[ -f random_01.md ]] || exit 1
[[ -f random_02.md ]] || exit 1
[[ -f random_03.md ]] || exit 1
[[ -f random_04.md ]] || exit 1
[[ -f random_05.md ]] || exit 1
[[ -f random_06.md ]] || exit 1
[[ -f random_07.md ]] || exit 1
[[ -f random_08.md ]] || exit 1
[[ -f random_09.md ]] || exit 1
[[ -f random_10.md ]] || exit 1
[[ -f random_11.md ]] || exit 1
[[ -f random_12.md ]] || exit 1
[[ -f random_13.md ]] || exit 1
[[ -f random_14.md ]] || exit 1
[[ -f random_15.md ]] || exit 1
[[ -f random_16.md ]] || exit 1
[[ -f random_17.md ]] || exit 1
[[ -f random_18.md ]] || exit 1
[[ -f random_19.md ]] || exit 1
[[ -f random_00.html ]] || exit 1
[[ -f random_01.html ]] || exit 1
[[ -f random_02.html ]] || exit 1
[[ -f random_03.html ]] || exit 1
[[ -f random_04.html ]] || exit 1
[[ -f random_05.html ]] || exit 1
[[ -f random_06.html ]] || exit 1
[[ -f random_07.html ]] || exit 1
[[ -f random_08.html ]] || exit 1
[[ -f random_09.html ]] || exit 1
[[ -f random_10.html ]] || exit 1
[[ -f random_11.html ]] || exit 1
[[ -f random_12.html ]] || exit 1
[[ -f random_13.html ]] || exit 1
[[ -f random_14.html ]] || exit 1
[[ -f random_15.html ]] || exit 1
[[ -f random_16.html ]] || exit 1
[[ -f random_17.html ]] || exit 1
[[ -f random_18.html ]] || exit 1
[[ -f random_19.html ]] || exit 1
