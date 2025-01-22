#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import cat_pdf

static("doc1.pdf", "doc2.pdf")
cat_pdf(["doc1.pdf", "doc2.pdf"], "cat.pdf")
