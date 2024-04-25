#!/usr/bin/env python
from stepup.core.api import static
from stepup.reprep.api import check_hrefs

static("README.md", "test.md", "check_hrefs.yaml")
check_hrefs("test.md")
