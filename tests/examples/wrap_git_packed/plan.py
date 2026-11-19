#!/usr/bin/env python3
from stepup.core.api import static
from stepup.reprep.api import wrap_git

static(".git/")
wrap_git("git rev-parse HEAD", stdout="head.txt")
