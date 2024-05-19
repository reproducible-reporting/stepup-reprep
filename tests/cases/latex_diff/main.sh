#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
xargs rm -rvf < .gitignore

# Run the example
stepup -w 1 plan.py & # > current_stdout.txt &

# Wait for the director and get its socket.
export STEPUP_DIRECTOR_SOCKET=$(
  python -c "import stepup.core.director; print(stepup.core.director.get_socket())"
)

# Get the graph after completion of the pending steps.
python3 - << EOD
from stepup.core.interact import *
wait()
graph("current_graph")
EOD

# Reproducibility test
mv diff.tex diff1.tex
python3 - << EOD
from stepup.core.interact import *
from stepup.reprep.make_inventory import write_inventory
watch_delete("diff.tex")
run()
join()
write_inventory("reproducibility_inventory.txt", ["diff.tex", "diff1.tex"])
EOD

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f diff.tex ]] || exit -1
[[ -f diff1.tex ]] || exit -1
[[ -f reproducibility_inventory.txt ]] || exit -1
