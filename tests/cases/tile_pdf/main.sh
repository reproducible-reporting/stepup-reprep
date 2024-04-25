#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
xargs rm -rvf < .gitignore

# Run the example
export SOURCE_DATE_EPOCH="315532800"
export PUBLIC="public/"
stepup -w 1 plan.py & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
python3 - << EOD
from stepup.core.interact import *
wait()
graph("current_graph.txt")
EOD

# Reproducibility test
mv figure.pdf figure1.pdf
python3 - << EOD
from stepup.core.interact import *
from stepup.reprep.make_manifest import write_manifest
watch_del("figure.pdf")
run()
join()
write_manifest("reproducibility_manifest.txt", ["figure.pdf", "figure1.pdf"])
EOD

# Wait for background processes, if any.
wait $(jobs -p)

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f triangle.svg ]] || exit -1
[[ -f square.svg ]] || exit -1
[[ -f pentagon.svg ]] || exit -1
[[ -f hexagon.svg ]] || exit -1
[[ -f vertical.svg ]] || exit -1
[[ -f horizontal.svg ]] || exit -1
[[ -f triangle.pdf ]] || exit -1
[[ -f square.pdf ]] || exit -1
[[ -f pentagon.pdf ]] || exit -1
[[ -f hexagon.pdf ]] || exit -1
[[ -f vertical.pdf ]] || exit -1
[[ -f horizontal.pdf ]] || exit -1
[[ -f figure.pdf ]] || exit -1
[[ -f figure1.pdf ]] || exit -1
[[ -f reproducibility_manifest.txt ]] || exit -1
