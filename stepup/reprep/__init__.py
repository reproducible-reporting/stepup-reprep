# SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""StepUp extension for Reproducible Reporting."""

from stepup.core.platform.stdio import write_utf8_unless_terminal

__all__ = ()

# Importing any module of this package makes the standard output and error
# write UTF-8 with `\n` line endings, unless they are a terminal,
# because StepUp decodes the output of every step as UTF-8.
write_utf8_unless_terminal()
