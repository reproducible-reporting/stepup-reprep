# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# © 2024–2025 Toon Verstraelen
#
# This file is part of StepUp RepRep.
#
# StepUp RepRep is free software;  you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# StepUp RepRep is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
r"""Identification of errors in LaTeX logs."""

import re
import sys

import attrs


@attrs.define
class ErrorInfo:
    program: str = attrs.field(validator=attrs.validators.instance_of(str))
    src: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    message: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )

    def print(self, log: str | None = None):
        print(f"\033[1;31;40m{self.program} ERROR\033[0;0m", file=sys.stderr)
        if log is not None:
            print(f"\033[1;35;40mLog file:\033[0;0m {log}", file=sys.stderr)
        if self.src is not None:
            print(f"\033[1;35;40mSource file:\033[0;0m {self.src}", file=sys.stderr)
        if self.message is not None:
            print(self.message, file=sys.stderr)


DEFAULT_MESSAGE = """\
> The error message could not be isolated from the file {path}.
> You can open the file {path} in a text editor and locate the error manually.
>
> Please open a new issue with the file {path} attached,
> which will help improve the script to detect the error message:
> https://github.com/reproducible-reporting/stepup-reprep/issues
>
> Thank you very much!
"""

MESSAGE_SUFFIX = """
> If the above extract from the log file can be improved,
> open a new issue with the file {path} attached:
> https://github.com/reproducible-reporting/stepup-reprep/issues
"""


@attrs.define
class LatexSourceStack:
    stack: list[str] = attrs.field(init=False, default=attrs.Factory(list))
    unfinished: str | None = attrs.field(init=False, default=None)
    unmatched: bool = attrs.field(init=False, default=False)

    @property
    def current(self) -> str:
        """The current file to which the error message belongs."""
        if len(self.stack) == 0:
            return "(could not detect source file)"
        return self.stack[-1]

    def feed(self, line: str):
        # Check if we need to anticipate line wrapping
        full = len(line) == 80
        if full:
            # Some exceptions: guess when 80-char lines end exactly with a filename.
            # This is fragile, but LaTeX log files are just a mess to parse.
            for end in ".tex\n", ".sty\n", ".cls\n", ".def\n", ".cfg\n", ".clo\n":
                if line.endswith(end):
                    full = False
                    break

        # Continue from previous line if needed
        if self.unfinished is not None:
            line = self.unfinished + line
            self.unfinished = None

        if full:
            self.unfinished = line[:-1]
            return

        # Update to stack
        brackets = re.findall(r"\((?:(?:\./|\.\./|/)[-_./a-zA-Z0-9]+)?|\)", line)
        for bracket in brackets:
            if bracket == ")":
                if len(self.stack) == 0:
                    self.unmatched = True
                else:
                    del self.stack[-1]
            else:
                if not bracket.startswith("("):
                    raise AssertionError("Inconsistent parenthesis logic in LatexSourceStack")
                self.stack.append(bracket[1:])


def parse_latex_log(path_log: str) -> ErrorInfo | None:
    """Parse a LaTeX log file.

    Parameters
    ----------
    path_log
        The log file

    Returns
    -------
    error_info
        Structured info for printing error, or None
    """
    lss = LatexSourceStack()
    src = "(could not detect source file)"
    record = False
    found_line = False
    recorded = []

    # LaTeX log files may have encoding errors, so such errors must be ignored.
    with open(path_log, errors="ignore") as fh:
        for line in fh.readlines():
            if record:
                recorded.append(line.rstrip())
                if recorded[-1].strip() == "":
                    record = False
                    if found_line:
                        break
            if line.startswith("!"):
                if not record:
                    recorded.append(line.rstrip())
                record = True
                src = lss.current
            elif line.startswith("l."):
                if not record:
                    recorded.append(line.rstrip())
                record = True
                found_line = True
            else:
                lss.feed(line)

    if len(recorded) > 0:
        message = "\n".join(recorded) + MESSAGE_SUFFIX.format(path=path_log)
    else:
        message = DEFAULT_MESSAGE.format(path=path_log)
    if lss.unmatched:
        message += "> [warning: unmatched closing parenthesis]\n"
    return ErrorInfo("LaTeX", src, message=message)


def update_last_src(line, last_src):
    if not ("(" in line or ")" in line or line.startswith("/")):
        last_src = line
    return last_src
