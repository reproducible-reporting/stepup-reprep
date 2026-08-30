#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import sync_zenodo

static("sync_zenodo.yaml", "zenodo_description.md", "README.txt")
sync_zenodo("sync_zenodo.yaml", ["README.txt"], path_description="zenodo_description.md")
