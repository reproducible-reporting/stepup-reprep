#!/usr/bin/env python

from stepup.core.api import static
from stepup.reprep.api import make_manifest

static("MANIFEST.in", "README.md", "hello.txt")
make_manifest("MANIFEST.in")
