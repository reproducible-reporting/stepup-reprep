#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import make_inventory, zip_inventory

static("inventory.def")

# Make all files in `data` static when they are needed.
static("data/")

make_inventory("inventory.txt", path_def="inventory.def")
zip_inventory("inventory.txt", "upload.zip")
