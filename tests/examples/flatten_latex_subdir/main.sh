#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
sb -w -j 1 & # > current_stdout.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph
stepup join

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f sub/article_structured.tex ]] || exit 1
[[ -f sub/part1.tex ]] || exit 1
[[ -f sub/part2.tex ]] || exit 1
[[ -f sub/article.tex ]] || exit 1
cp sub/article.tex current_article.tex

# Create an inventory file
srr-make-inventory -i inventory.def -o current_inventory.txt

# Wait for background processes, if any.
wait
