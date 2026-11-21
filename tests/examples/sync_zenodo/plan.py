#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import make_inventory, sync_zenodo

static("sync_zenodo.yaml", "zenodo_description.md", "README.txt")
make_inventory("README.txt", "zenodo_inventory.jsonl")
sync_zenodo("sync_zenodo.yaml", "zenodo_description.md", "zenodo_inventory.jsonl")
