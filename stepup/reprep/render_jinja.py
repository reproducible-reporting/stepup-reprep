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
"""Rendering of template files with Jinja2.

Parameters for the template can be defined in a "variables" Python file,
from which all variables that are strings, integers or floats are imported.
"""

import argparse
import contextlib
import importlib.util
import json
import sys
from types import ModuleType

import jinja2
import yaml
from path import Path


def main(argv: list[str] | None = None):
    """Main program."""
    args = parse_args(argv)
    if args.mode == "plain":
        latex = False
    elif args.mode == "latex":
        latex = True
    elif args.mode == "auto":
        latex = args.path_out.endswith(".tex")
    else:
        raise ValueError(f"mode not supported: {args.mode}")
    dir_out = Path(args.path_out).parent.absolute()
    variables = load_variables(args.paths_variables, dir_out)
    if args.json is not None:
        variables.update(json.loads(args.json))
    result = render(args.path_in, variables, latex)
    with open(args.path_out, "w") as fh:
        fh.write(result)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(prog="rr-render", description="Render a file with Jinja2.")
    parser.add_argument("path_in", help="The input file")
    parser.add_argument(
        "paths_variables",
        nargs="*",
        type=Path,
        help="Python, JSON or YAML files defining variables."
        "They are loaded in the given order, "
        "so later variable definitions may overrule earlier ones. "
        "Python files have the advantage of supporting more types and logic. "
        "path.Path instances are interpreted as relative to parent of the variable file.",
    )
    parser.add_argument("path_out", help="The output file")
    parser.add_argument(
        "--mode",
        choices=["auto", "plain", "latex"],
        help="The delimiter style to use",
        default="auto",
    )
    parser.add_argument(
        "--json",
        help="Variables are given as a JSON string (overrules the variables files)",
    )
    return parser.parse_args(argv)


def load_variables(paths_variables: list[str], dir_out: str) -> dict[str, str]:
    """Load user-defined variable from Python files.

    Parameters
    ----------
    paths_variables
        paths of Python, JSON or YAML files containing variable definitions.
        They are loaded in the given order, so later variable definitions may overrule earlier ones.
    dir_out
        This is used to translate paths defined the variables files to relative paths with respect
        to the parent of the output of the rendering task.

    Returns
    -------
    variables
        A dictionary with variables.
    """
    variables = {}
    for path_var in paths_variables:
        path_var = Path(path_var)
        if path_var.suffix == ".json":
            with open(path_var) as fh:
                variables.update(json.load(fh))
        elif path_var.suffix in (".yaml", ".yml"):
            with open(path_var) as fh:
                variables.update(yaml.safe_load(fh))
        elif path_var.suffix == ".py":
            dir_py = path_var.parent.normpath()
            fn_py = path_var.name
            with contextlib.chdir(dir_py):
                module = load_module_file(fn_py, "variables")
                current = vars(module)
            for name, value in current.items():
                if isinstance(value, (str | int | float | None)):
                    if isinstance(value, Path):
                        value = value.relpath(dir_out)
                    variables[name] = value
        else:
            raise ValueError(f"unsupported variable file format: {path_var}")
    return variables


def load_module_file(path_py: str, name: str = "pythonscript") -> ModuleType:
    """Load a Python module from a given path."""
    parent = Path(path_py).parent
    sys.path.append(parent)
    try:
        spec = importlib.util.spec_from_file_location(f"<{name}>", str(path_py))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(parent)
    return module


def render(
    path_template: str,
    variables: dict[str, str],
    latex: bool = False,
    *,
    str_in: str | None = None,
) -> str:
    """The template is processed with jinja and returned after filling in variables.

    Parameters
    ----------
    path_template
        The filename of the template to load, may be a mock
    variables
        A dictionary of variables to substitute into the template.
    latex
        When True, the angle-version of the template codes is used, e.g. `<%` etc.
    str_in
        The template string.
        When given path_templates is not loaded and only used for error messages.

    Returns
    -------
    str_out
        A string with the result.
    """
    # Customize Jinja 2 environment
    env_kwargs = {
        "keep_trailing_newline": True,
        "trim_blocks": True,
        "undefined": jinja2.StrictUndefined,
        "autoescape": False,
    }
    if latex:
        env_kwargs.update(
            {
                "block_start_string": "<%",
                "block_end_string": "%>",
                "variable_start_string": "<<",
                "variable_end_string": ">>",
                "comment_start_string": "<#",
                "comment_end_string": "#>",
                "line_statement_prefix": "%==",
            }
        )
    env = jinja2.Environment(**env_kwargs)

    # Load template and use it
    if str_in is None:
        with open(path_template) as f:
            str_in = f.read()
    template = env.from_string(str_in)
    template.filename = path_template
    return template.render(**variables)


if __name__ == "__main__":
    main(sys.argv[1:])
