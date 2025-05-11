#!/usr/bin/env python3
from stepup.core.api import runsh, static
from stepup.reprep.api import make_inventory, zip_inventory

static("static.txt")
runsh("echo hello > ${out}", out="built.txt")
make_inventory("static.txt", "built.txt", "inventory.txt")
zip_inventory("inventory.txt", "upload.zip")
