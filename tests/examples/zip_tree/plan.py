#!/usr/bin/env python3
from stepup.core.api import glob
from stepup.reprep.api import make_inventory, zip_inventory

# Make all subdirectories in `data` static when they are needed.
glob("data/**/", _defer=True)

# Make all .out files in data static with a recursive glob.
# Containing directories and their parents also become static due to the deferred glob.
out_files = glob("data/**/*.out")

# Create an inventory file with all .out files and zip it.
make_inventory(*out_files, "inventory.txt")
zip_inventory("inventory.txt", "upload.zip")
