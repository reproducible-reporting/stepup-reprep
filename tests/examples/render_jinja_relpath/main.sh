#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
export SOURCE_DATE_EPOCH="315532800"
export PUBLIC="public/"
stepup -w -n 1 plan.py & # > current_stdout.txt &

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
[[ -f variables.py ]] || exit 1
[[ -f static/main.tex ]] || exit 1
[[ -f static/plan.py ]] || exit 1
[[ -f static/preamble.inc.tex ]] || exit 1
[[ -f static/variables.py ]] || exit 1
[[ -f public/preamble.inc.tex ]] || exit 1
[[ -f public/main.pdf ]] || exit 1
[[ -f public/main.tex ]] || exit 1
grep Everything public/main.tex
