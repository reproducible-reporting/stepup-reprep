#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import wrap_git

static(".git/")
wrap_git("git log -n1 --pretty='format:%cs (%h)'", stdout="gitlog.txt")
