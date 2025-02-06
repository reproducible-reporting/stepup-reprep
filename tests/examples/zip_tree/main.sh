#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Create a data directory used as static files.
mkdir -p data/sub/deeper
echo "blabla" > data/bla.inp
echo "brrrr" > data/sub/deeper/brrr.inp
echo "works" > data/sub/works.out
echo "fine" > data/fine.out
echo "nested" > data/sub/deeper/nested.out

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

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f inventory.txt ]] || exit 1
[[ -f upload.zip ]] || exit 1
[[ $(wc -l inventory.txt | cut -d' ' -f1) -eq 3 ]] || exit 1
