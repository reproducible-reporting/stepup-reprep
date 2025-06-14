#!/usr/bin/env -S bash -x
# Exit on first error and cleanup.
set -e
trap 'kill $(pgrep -g $$ | grep -v $$) > /dev/null 2> /dev/null || :' EXIT
rm -rf .git
rm -rvf $(cat .gitignore)

# Prepare a git repo
git init --initial-branch=main
git config user.email "tester@no-email.com"
git config user.name "Tester"
touch foo.txt
git add -f foo.txt
git commit -m "Initial commit with foo.txt"

# Run the example
stepup boot -w -n 1 & # > current_stdout_1.txt &
PID=$!

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph_1
stepup join

# Wait for background processes, if any.
set +e; wait -fn $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f gitlog.txt ]] || exit 1

cp gitlog.txt gitlog-1.txt

# Create another commit
echo "Some content" > foo.txt
git add foo.txt
git commit -m "Update foo.txt with some content"

# Run the example again
stepup boot -w -n 1 & # > current_stdout_2.txt &
PID=$!

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph_2
stepup join

# Wait for background processes, if any.
set +e; wait -fn $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f gitlog.txt ]] || exit 1

# Check that the gitlog.txt file has been updated.
cmp gitlog.txt gitlog-1.txt && exit 1
rm -rf .git
