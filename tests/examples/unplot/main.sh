#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Wait for background processes, if any.
wait

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f current_plot1.json ]] || exit 1
[[ -f current_plot2.json ]] || exit 1
./validate-unplot.py reference_plot1.json current_plot1.json
./validate-unplot.py reference_plot2.json current_plot2.json
