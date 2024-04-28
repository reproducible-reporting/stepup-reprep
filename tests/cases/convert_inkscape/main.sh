#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
xargs rm -rvf < .gitignore

# Run the example
export SOURCE_DATE_EPOCH="315532800"
stepup -w 1 plan.py & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
python3 - << EOD
from stepup.core.interact import *
wait()
graph("current_graph")
EOD

# Reproducibility test
mv final.pdf final1.pdf
mv glasses.png glasses1.png
python3 - << EOD
from stepup.core.interact import *
from stepup.reprep.make_manifest import write_manifest
watch_delete("final.pdf")
watch_delete("glasses.png")
run()
join()
write_manifest("reproducibility_png_manifest.txt", ["glasses.png", "glasses1.png"])
write_manifest("reproducibility_pdf_manifest.txt", ["final.pdf", "final1.pdf"])
EOD

# Wait for background processes, if any.
wait $(jobs -p)

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f smile.svg ]] || exit -1
[[ -f final.pdf ]] || exit -1
[[ -f final1.pdf ]] || exit -1
[[ -f reproducibility_pdf_manifest.txt ]] || exit -1
[[ -f reproducibility_png_manifest.txt ]] || exit -1
