#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
export SOURCE_DATE_EPOCH="315532800"
stepup -w -n 20 plan.py & # > current_stdout.txt &

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
[[ -f dots_050.svg ]] || exit 1
[[ -f dots_055.svg ]] || exit 1
[[ -f dots_060.svg ]] || exit 1
[[ -f dots_065.svg ]] || exit 1
[[ -f dots_070.svg ]] || exit 1
[[ -f dots_075.svg ]] || exit 1
[[ -f dots_080.svg ]] || exit 1
[[ -f dots_085.svg ]] || exit 1
[[ -f dots_090.svg ]] || exit 1
[[ -f dots_095.svg ]] || exit 1
[[ -f dots_100.svg ]] || exit 1
[[ -f dots_105.svg ]] || exit 1
[[ -f dots_110.svg ]] || exit 1
[[ -f dots_115.svg ]] || exit 1
[[ -f dots_120.svg ]] || exit 1
[[ -f dots_125.svg ]] || exit 1
[[ -f dots_130.svg ]] || exit 1
[[ -f dots_135.svg ]] || exit 1
[[ -f dots_140.svg ]] || exit 1
[[ -f dots_145.svg ]] || exit 1
[[ -f dots_050.pdf ]] || exit 1
[[ -f dots_055.pdf ]] || exit 1
[[ -f dots_060.pdf ]] || exit 1
[[ -f dots_065.pdf ]] || exit 1
[[ -f dots_070.pdf ]] || exit 1
[[ -f dots_075.pdf ]] || exit 1
[[ -f dots_080.pdf ]] || exit 1
[[ -f dots_085.pdf ]] || exit 1
[[ -f dots_090.pdf ]] || exit 1
[[ -f dots_095.pdf ]] || exit 1
[[ -f dots_100.pdf ]] || exit 1
[[ -f dots_105.pdf ]] || exit 1
[[ -f dots_110.pdf ]] || exit 1
[[ -f dots_115.pdf ]] || exit 1
[[ -f dots_120.pdf ]] || exit 1
[[ -f dots_125.pdf ]] || exit 1
[[ -f dots_130.pdf ]] || exit 1
[[ -f dots_135.pdf ]] || exit 1
[[ -f dots_140.pdf ]] || exit 1
[[ -f dots_145.pdf ]] || exit 1
