#!/usr/bin/env python
from stepup.core.api import static, step
from stepup.reprep.api import make_manifest, zip_manifest

static("static.txt")
step("echo hello > ${out}", out="built.txt")
make_manifest("MANIFEST.txt", ["static.txt", "built.txt"])
zip_manifest("MANIFEST.txt", "upload.zip")
