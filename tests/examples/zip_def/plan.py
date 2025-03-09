#!/usr/bin/env python3
from stepup.core.api import glob, static
from stepup.reprep.api import make_inventory, zip_inventory

static("inventory.def")

# Make all file in `data` static when they are needed.
glob("data/**", _defer=True)

# Create an inventory file with all files defined in `inventory.def`.
make_inventory("inventory.txt", path_def="inventory.def")
zip_inventory("inventory.txt", "upload.zip")
