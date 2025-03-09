#!/usr/bin/env python3
from stepup.core.api import static, step
from stepup.reprep.api import make_inventory, zip_inventory

static("static.txt")
step("echo hello > ${out}", out="built.txt")
make_inventory("static.txt", "built.txt", "inventory.txt")
zip_inventory("inventory.txt", "upload.zip")
