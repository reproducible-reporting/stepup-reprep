#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
xargs rm -rvf < .gitignore

# Run the example
stepup -w 1 plan.py & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
python3 - << EOD
from stepup.core.interact import *
wait()
graph("current_graph.txt")
EOD

# Reproducibility test
mv dst.pdf dst1.pdf
python3 - << EOD
from stepup.core.interact import *
from stepup.reprep.make_manifest import write_manifest
watch_del("dst.pdf")
run()
join()
write_manifest("reproducibility_manifest.txt", ["dst.pdf", "dst1.pdf"])
EOD

# Wait for background processes, if any.
wait $(jobs -p)

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f src.pdf ]] || exit -1
[[ -f notes.pdf ]] || exit -1
[[ -f dst.pdf ]] || exit -1
[[ -f dst1.pdf ]] || exit -1
[[ -f reproducibility_manifest.txt ]] || exit -1
