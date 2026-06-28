#!/usr/bin/env -S bash -x
source ../example.rc

# Run the example
cp plan1.py plan.py
sb -w -j 1 & # > current_stdout1.txt &

# Get the graph after completion of the pending steps.
stepup wait
stepup graph current_graph1
stepup join

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f article_structured.tex ]] || exit 1
[[ ! -f article.tex ]] || exit 1

# Wait for background processes, if any.
wait

# Add the missing file and run again
cp plan2.py plan.py
cp sub/original.tex sub/other.tex
rm .stepup/*.log
sb -w -j 1 & # > current_stdout2.txt &

# Wait for the director and get its socket.
stepup wait
stepup graph current_graph2
stepup join

# Check files that are expected to be present and/or missing.
[[ -f plan.py ]] || exit 1
[[ -f article_structured.tex ]] || exit 1
[[ -f article.tex ]] || exit 1
mv article.tex current_article.tex

# Wait for background processes, if any.
wait
