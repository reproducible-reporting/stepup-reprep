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
join()
EOD

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit -1
[[ -f sub/article_structured.tex ]] || exit -1
[[ -f sub/part1.tex ]] || exit -1
[[ -f sub/part2.tex ]] || exit -1
[[ -f sub/article.tex ]] || exit -1
cp sub/article.tex current_article.tex

# Wait for background processes, if any.
wait $(jobs -p)
