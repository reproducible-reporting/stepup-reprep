#!/usr/bin/env python3
from stepup.core.api import run, static
from stepup.reprep.api import make_inventory, zip_inventory

static("static.txt")
run("echo hello > built.txt", out="built.txt", shell=True)
make_inventory("static.txt", "built.txt", "inventory.txt")
zip_inventory("inventory.txt", "upload.zip")
