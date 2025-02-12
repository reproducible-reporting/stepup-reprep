#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
export SOURCE_DATE_EPOCH="315532800"
stepup -w -n 1 plan.py & # > current_stdout.txt &

# Wait for the director and get its socket.
export STEPUP_DIRECTOR_SOCKET=$(
  python -c "import stepup.core.director; print(stepup.core.director.get_socket())"
)
PID=$!

# Get the graph after completion of the pending steps.
python3 - << EOD
from stepup.core.interact import *
wait()
graph("current_graph")
EOD

# Reproducibility test
mv sub/demo.html sub/demo1.html
python3 - << EOD
from stepup.core.interact import *
from stepup.reprep.make_inventory import write_inventory
watch_delete("sub/demo.html")
run()
join()
write_inventory("reproducibility_inventory.txt", ["sub/demo.html", "sub/demo1.html"])
EOD

# Wait for background processes, if any.
set +e; wait -fn $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f sub/demo.md ]] || exit 1
[[ -f sub/demo.html ]] || exit 1
[[ -f sub/demo1.html ]] || exit 1
[[ -f reproducibility_inventory.txt ]] || exit 1
