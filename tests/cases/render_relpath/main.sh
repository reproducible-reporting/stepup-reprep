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
graph("current_graph")
join()
EOD

# Wait for background processes, if any.
wait $(jobs -p)

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f variables.py ]] || exit -1
[[ -f static/main.tex ]] || exit -1
[[ -f static/plan.py ]] || exit -1
[[ -f static/preamble.inc.tex ]] || exit -1
[[ -f static/variables.py ]] || exit -1
[[ -f public/preamble.inc.tex ]] || exit -1
[[ -f public/main.pdf ]] || exit -1
[[ -f public/main.tex ]] || exit -1
grep Everything public/main.tex
