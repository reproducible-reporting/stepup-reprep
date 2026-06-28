#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example with first snippet: snippet1.tex
cp snippet1.tex snippet.tex
sb -w -j 1 & # > current_stdout1.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph1
stepup join

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f dest/snippet.tex ]] || exit 1
[[ -f dest/first.dat ]] || exit 1
[[ ! -f dest/second.dat ]] || exit 1


# Run the example with second snippet: snippet2.tex
cp snippet2.tex snippet.tex
sb -w -j 1 & # > current_stdout2.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph2
stepup join

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f dest/snippet.tex ]] || exit 1
[[ -f dest/first.dat ]] || exit 1
[[ -f dest/second.dat ]] || exit 1
