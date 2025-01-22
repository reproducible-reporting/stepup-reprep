#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import sync_zenodo

static("zenodo.yaml", "zenodo.md", "README.md")
sync_zenodo("zenodo.yaml")
