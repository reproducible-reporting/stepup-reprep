#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rvf $(cat .gitignore)

# Run the example
export SOURCE_DATE_EPOCH="315532800"
stepup -w -n 20 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f something.odt ]] || exit 1
[[ -f copy_00.odt ]] || exit 1
[[ -f copy_01.odt ]] || exit 1
[[ -f copy_02.odt ]] || exit 1
[[ -f copy_03.odt ]] || exit 1
[[ -f copy_04.odt ]] || exit 1
[[ -f copy_05.odt ]] || exit 1
[[ -f copy_06.odt ]] || exit 1
[[ -f copy_07.odt ]] || exit 1
[[ -f copy_08.odt ]] || exit 1
[[ -f copy_09.odt ]] || exit 1
[[ -f copy_10.odt ]] || exit 1
[[ -f copy_11.odt ]] || exit 1
[[ -f copy_12.odt ]] || exit 1
[[ -f copy_13.odt ]] || exit 1
[[ -f copy_14.odt ]] || exit 1
[[ -f copy_15.odt ]] || exit 1
[[ -f copy_16.odt ]] || exit 1
[[ -f copy_17.odt ]] || exit 1
[[ -f copy_18.odt ]] || exit 1
[[ -f copy_19.odt ]] || exit 1
[[ -f copy_00.pdf ]] || exit 1
[[ -f copy_01.pdf ]] || exit 1
[[ -f copy_02.pdf ]] || exit 1
[[ -f copy_03.pdf ]] || exit 1
[[ -f copy_04.pdf ]] || exit 1
[[ -f copy_05.pdf ]] || exit 1
[[ -f copy_06.pdf ]] || exit 1
[[ -f copy_07.pdf ]] || exit 1
[[ -f copy_08.pdf ]] || exit 1
[[ -f copy_09.pdf ]] || exit 1
[[ -f copy_10.pdf ]] || exit 1
[[ -f copy_11.pdf ]] || exit 1
[[ -f copy_12.pdf ]] || exit 1
[[ -f copy_13.pdf ]] || exit 1
[[ -f copy_14.pdf ]] || exit 1
[[ -f copy_15.pdf ]] || exit 1
[[ -f copy_16.pdf ]] || exit 1
[[ -f copy_17.pdf ]] || exit 1
[[ -f copy_18.pdf ]] || exit 1
[[ -f copy_19.pdf ]] || exit 1
