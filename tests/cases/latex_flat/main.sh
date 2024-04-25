#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
xargs rm -rvf < .gitignore

# Run the example
cp plan_01.py plan.py
stepup -w 1 plan.py & # > current_stdout_01.txt &

# Get the graph after completion of the pending steps.
python3 - << EOD
from stepup.core.interact import *
print("HERE")
wait()
graph("current_graph_01.txt")
join()
EOD

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f article_structured.tex ]] || exit -1
[[ ! -f article.tex ]] || exit -1

# Wait for background processes, if any.
wait $(jobs -p)

# Add the missing file and run again
cp plan_02.py plan.py
cp sub/original.tex sub/other.tex
stepup -w 1 plan.py & # > current_stdout_02.txt &
python3 - << EOD
from stepup.core.interact import *
wait()
graph("current_graph_02.txt")
join()
EOD

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f article_structured.tex ]] || exit -1
[[ -f article.tex ]] || exit -1

# Wait for background processes, if any.
wait $(jobs -p)
