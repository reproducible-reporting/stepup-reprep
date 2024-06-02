# StepUp RepRep is the StepUp extension for Reproducible Reporting.
# Copyright (C) 2024 Toon Verstraelen
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
r"""Identification of dependencies from LaTeX sources."""

import re

from path import Path

RE_OPTIONS = re.MULTILINE | re.DOTALL
RE_INPUT = re.compile(r"\\input\s*\{([^}]*)}", RE_OPTIONS)
RE_VERBATIMINPUT = re.compile(r"\\verbatiminput\s*\{([^}]*)}", RE_OPTIONS)
RE_INCLUDEGRAPHICS = re.compile(r"\\includegraphics(?:\s*\[[^]]*])?\s*\{([^}]*)}", RE_OPTIONS)
RE_BIBLIOGRAPHY = re.compile(r"\\bibliography\s*\{([^}]*)}", RE_OPTIONS)
RE_IMPORT = re.compile(r"\\import\s*\{([^}]*)}\s*\{([^}]*)}", RE_OPTIONS)


def cleanup_path(path, ext=None):
    """Clean up a path of a dependency extracted from a LaTeX source.

    Parameters
    ----------
    path
        The path derived from the LaTeX source.
    ext
        The extension to be added

    Returns
    -------
    path_clean
        A cleaned up file name, including the path of the dirname.
    """
    path = path.replace("{", "")
    path = path.replace("}", "")
    path = re.sub(r"\s+", " ", path)
    path = Path(path.strip())
    if "." not in path.basename() and ext is not None:
        path = path.with_suffix(ext)
    return path.normpath()


def iter_latex_references(tex_no_comments):
    r"""Loop over file references in a TeX source without comments.

    Parameters
    ----------
    tex_no_comments
        The contents of a TeX source files from which comments were stripped.

    Yields
    ------
    relative_path
        The change in current directory implied by a TeX command.
        (This is only relevant for \import, no change in directory otherwise.)
    filename
        The filename of the file included, may include directory.
    ext
        The extension one may add if not given.
        (Approximate guess, because the correct extension for figures
        depends on details of the LaTeX compiler.)
    """
    for fn_inc in re.findall(RE_INPUT, tex_no_comments):
        yield ".", fn_inc, ".tex"
    for fn_inc in re.findall(RE_VERBATIMINPUT, tex_no_comments):
        yield ".", fn_inc, ".txt"
    for fn_inc in re.findall(RE_INCLUDEGRAPHICS, tex_no_comments):
        yield ".", fn_inc, ".pdf"
    for fn_inc in re.findall(RE_BIBLIOGRAPHY, tex_no_comments):
        yield ".", fn_inc, ".bib"
    for new_root, fn_inc in re.findall(RE_IMPORT, tex_no_comments):
        yield new_root, fn_inc, ".tex"


def scan_latex_deps(path_tex, tex_root=None):
    """Scan LaTeX source code for dependencies.

    Parameters
    ----------
    path_tex
        The path to the LaTeX source to scan.
    tex_root
        The directory with respect to which the latex file references should be interpreted.

    Returns
    -------
    implicit
        Filenames to be added to the implicit dependencies.
    bib
        BibTeX files.
    """
    implicit = set()
    bib = set()

    path_tex = Path(path_tex)
    if path_tex.is_file():
        tex_root = path_tex.parent.normpath() if tex_root is None else Path(tex_root)
        with open(path_tex) as fh:
            stripped = []
            for line in fh:
                if "%REPREP ignore" in line:
                    pass
                elif line.startswith("%REPREP input "):
                    implicit.add((tex_root / line[13:].strip()).normpath())
                else:
                    stripped.append(line[: line.find("%")].rstrip())

            # Process the file references
            for new_root, fn_inc, ext in iter_latex_references("\n".join(stripped)):
                new_root = (tex_root / cleanup_path(new_root)).normpath()
                path_inc = (new_root / cleanup_path(fn_inc, ext)).normpath()
                if ext == ".bib":
                    bib.add(path_inc)
                else:
                    implicit.add(path_inc)
                if ext == ".tex":
                    sub_implicit, sub_bib = scan_latex_deps(path_inc, new_root)
                    implicit.update(sub_implicit)
                    bib.update(sub_bib)
    return sorted(implicit), sorted(bib)
