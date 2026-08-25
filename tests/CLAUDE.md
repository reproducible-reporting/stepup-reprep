<!--
SPDX-FileCopyrightText: 2024 Toon Verstraelen <Toon.Verstraelen@UGent.be>
SPDX-License-Identifier: LGPL-3.0-or-later
-->

# Test Structure

## Integration Examples

Example tests copy a fixture directory to a temporary directory, run StepUp there,
then compare the outputs against the `expected/` subdirectories.

## Regenerating Expected Outputs

```bash
STEPUP_OVERWRITE_EXPECTED=1 pytest -vv tests/test_examples.py
```

The same variable is honored by `tests/test_bibparser.py` and `tests/test_bibsane.py`.
