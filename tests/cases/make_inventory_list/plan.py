#!/usr/bin/env python

from stepup.core.api import static
from stepup.reprep.api import make_inventory

static("README.md")
make_inventory(["README.md"], "inventory.txt")
