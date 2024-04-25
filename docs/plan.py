#!/usr/bin/env python
from path import Path

from stepup.core.api import static, step


def plan_tutorial(tutdir: str, out: list[str]):
    """Define static files and a step for running a tutorial example."""
    workdir = Path(tutdir)
    main = workdir / "main.sh"
    plan = workdir / "plan.py"
    static(workdir, main, plan)
    out = [workdir / out_path for out_path in out]
    step("./main.sh", workdir=workdir, inp=[main, plan], out=out)
    return out


static("tutorials/")
tutout = [
    *plan_tutorial("tutorials/tile_pdf/", ["stdout.txt"]),
]

# step("mkdocs build", workdir="../", inp=tutout)
