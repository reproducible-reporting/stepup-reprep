#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import add_notes_pdf

static("src.pdf", "notes.pdf")
add_notes_pdf("src.pdf", "notes.pdf", "dst.pdf")
