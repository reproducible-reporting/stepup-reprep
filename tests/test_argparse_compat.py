# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unit tests for stepup.reprep.argparse_compat, through the parsers that rely on it."""

from stepup.reprep.compile_tectonic import parse_args as parse_args_tectonic
from stepup.reprep.compile_typst import parse_args as parse_args_typst
from stepup.reprep.convert_inkscape import parse_args as parse_args_inkscape


def test_typst_out_before_dashdash():
    args = parse_args_typst(["main.typ", "--out=x.pdf", "--", "--ppi", "300"])
    assert args.path_typ == "main.typ"
    assert args.path_out == "x.pdf"
    assert args.typst_args == ["--ppi", "300"]


def test_typst_sysinp_before_dashdash():
    args = parse_args_typst(["main.typ", "--sysinp", "a=1", "b=2", "--", "--ppi", "300"])
    assert args.path_typ == "main.typ"
    assert args.sysinp == ["a=1", "b=2"]
    assert args.typst_args == ["--ppi", "300"]


def test_typst_without_args():
    args = parse_args_typst(["main.typ", "--out=x.pdf"])
    assert args.path_typ == "main.typ"
    assert args.typst_args == []


def test_inkscape_option_before_dashdash():
    args = parse_args_inkscape(["a.svg", "a.pdf", "--inkscape=ink", "--", "-T"])
    assert args.path_svg == "a.svg"
    assert args.path_out == "a.pdf"
    assert args.inkscape == "ink"
    assert args.inkscape_args == ["-T"]


def test_tectonic_option_before_dashdash():
    args = parse_args_tectonic(["main.tex", "--outdir=out/", "--", "-Z", "shell-escape"])
    assert args.path_tex == "main.tex"
    assert args.outdir == "out/"
    assert args.tectonic_args == ["-Z", "shell-escape"]
