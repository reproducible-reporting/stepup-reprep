#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import check_hrefs

static("README.txt", "test.html", "check_hrefs.yaml")
check_hrefs("test.html")
