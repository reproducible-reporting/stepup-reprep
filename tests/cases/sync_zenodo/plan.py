#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import sync_zenodo

static("zenodo.yaml", "zenodo.md", "README.md")
sync_zenodo("zenodo.yaml")
