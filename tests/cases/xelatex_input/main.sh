#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
xargs rm -rvf < .gitignore

# Run the example
export SOURCE_DATE_EPOCH="315532800"
export REPREP_LATEX="xelatex"
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
rm paper.aux
rm paper.log
rm subdir/generated.tex
rm subdir/code.txt
mv paper.pdf paper1.pdf
python3 - << EOD
from stepup.core.interact import *
from stepup.reprep.make_inventory import write_inventory
watch_delete("paper.pdf")
watch_delete("subdir/generated.tex")
watch_delete("subdir/code.txt")
run()
join()
write_inventory("reproducibility_inventory.txt", ["paper.pdf", "paper1.pdf"])
EOD

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f paper.pdf ]] || exit -1
[[ -f paper.log ]] || exit -1
[[ -f paper.aux ]] || exit -1
[[ -f paper1.pdf ]] || exit -1
[[ -f reproducibility_inventory.txt ]] || exit -1
reprep-check-inventory paper-inventory.txt
