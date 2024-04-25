#!/usr/bin/env python

from stepup.core.api import static
from stepup.reprep.api import make_manifest

static("README.md")
make_manifest("MANIFEST.txt", "README.md")
