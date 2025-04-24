#!/usr/bin/env python3

from stepup.core.api import static
from stepup.reprep.api import make_inventory

static("README.txt")
make_inventory("README.txt", "inventory.txt")
