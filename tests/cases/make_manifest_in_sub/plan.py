#!/usr/bin/env python

from stepup.core.api import static
from stepup.reprep.api import make_manifest

static("sub/", "sub/MANIFEST.in", "sub/hello.txt")
make_manifest("sub/MANIFEST.in")
