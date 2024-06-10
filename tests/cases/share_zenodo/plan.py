#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import share_zenodo

static("zenodo.yaml", "zenodo.md", "README.md")
share_zenodo("zenodo.yaml")
