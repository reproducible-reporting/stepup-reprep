#!/usr/bin/env -S bash -x
source ../example.rc

# Prepare a git repo with one commit and move all refs into .git/packed-refs, as `git gc` does.
# Fixed dates make the commit ids, and hence the digests of git files in the output, reproducible.
export GIT_AUTHOR_DATE="2026-01-01T00:00:00Z"
export GIT_COMMITTER_DATE="2026-01-01T00:00:00Z"
git init --initial-branch=main
git config user.email "tester@no-email.com"
git config user.name "Tester"
echo "First" > foo.txt
git add -f foo.txt
git commit -m "First commit"
git pack-refs --all
[[ -f .git/refs/heads/main ]] && exit 1

# Run the example
sb -w -j 1 & # > current_stdout_1.txt &
PID=$!

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph_1
stepup join

# Wait for background processes, if any.
set +e; wait $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check that head.txt contains the tip of the branch.
[[ "$(cat head.txt)" == "$(git rev-parse main)" ]] || exit 1

# Create another commit, which writes a loose ref and leaves .git/packed-refs unchanged.
echo "Second" > foo.txt
git add foo.txt
git commit -m "Second commit"
[[ -f .git/refs/heads/main ]] || exit 1

# Run the example again
sb -w -j 1 & # > current_stdout_2.txt &
PID=$!

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph_2
stepup join

# Wait for background processes, if any.
set +e; wait $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check that head.txt contains the new tip of the branch.
[[ "$(cat head.txt)" == "$(git rev-parse main)" ]] || exit 1

# Pack the refs again, which removes the loose ref.
git pack-refs --all
[[ -f .git/refs/heads/main ]] && exit 1

# Run the example again
sb -w -j 1 & # > current_stdout_3.txt &
PID=$!

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph_3
stepup join

# Wait for background processes, if any.
set +e; wait $PID; RETURNCODE=$?; set -e
[[ "${RETURNCODE}" -eq 0 ]] || exit 1

# Check that head.txt still contains the tip of the branch.
[[ "$(cat head.txt)" == "$(git rev-parse main)" ]] || exit 1
rm -rf .git
