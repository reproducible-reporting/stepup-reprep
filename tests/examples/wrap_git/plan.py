#!/usr/bin/env python3
from stepup.core.api import glob
from stepup.reprep.api import wrap_git

glob(".git/**", _defer=True)
wrap_git("git log -n1 --pretty='format:%cs (%h)'", out="gitlog.txt")
