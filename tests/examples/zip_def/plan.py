#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import make_inventory, zip_inventory

# Make all files in `data` static when they are needed.
static("inventory.def", "data/")

make_inventory("inventory.txt", path_def="inventory.def")
zip_inventory("inventory.txt", "upload.zip")
