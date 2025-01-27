#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
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

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f sub/article_structured.tex ]] || exit 1
[[ -f sub/part1.tex ]] || exit 1
[[ -f sub/part2.tex ]] || exit 1
[[ -f sub/article.tex ]] || exit 1
cp sub/article.tex current_article.tex

# Create an inventory file
rr-make-inventory -i inventory.def -o current_inventory.txt

# Wait for background processes, if any.
wait
