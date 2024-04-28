#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
xargs rm -rvf < .gitignore

# Run the example
export SOURCE_DATE_EPOCH="315532800"
export REPREP_LATEX="xelatex"
stepup -w 1 plan.py & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
python3 - << EOD
from stepup.core.interact import *
wait()
graph("current_graph")
EOD

# Reproducibility test
rm paper.aux
rm paper.log
rm subdir/generated.tex
rm subdir/code.txt
mv paper.pdf paper1.pdf
python3 - << EOD
from stepup.core.interact import *
from stepup.reprep.make_manifest import write_manifest
watch_delete("paper.pdf")
watch_delete("subdir/generated.tex")
watch_delete("subdir/code.txt")
run()
join()
write_manifest("reproducibility_manifest.txt", ["paper.pdf", "paper1.pdf"])
EOD

# Wait for background processes, if any.
wait $(jobs -p)

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f paper.pdf ]] || exit -1
[[ -f paper.log ]] || exit -1
[[ -f paper.aux ]] || exit -1
[[ -f paper1.pdf ]] || exit -1
[[ -f reproducibility_manifest.txt ]] || exit -1
reprep-check-manifest paper.MANIFEST.txt
