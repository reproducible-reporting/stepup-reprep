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
"""Unit tests for stepup.reprep.unplot."""

import json

from stepup.reprep.unplot import main


def test_bearing_speed_effect(path_tmp):
    # Plot taken from:
    # https://en.m.wikipedia.org/wiki/File:Measured_Bearing_Speed_Effect_data_and_curve.jpg
    path_out = path_tmp / "out.json"
    main(["docs/advanced_topics/unplot/plot.svg", path_out])
    with open(path_out) as fh:
        curves = json.load(fh)
    x = curves["measured"][0]
    y = curves["measured"][1]
    assert abs(x[0] - 199) < 1
    assert abs(y[0] - 165) < 1
    assert abs(x[-1] - 1099) < 1
    assert abs(y[-1] - 382) < 1
    assert len(x) == 10
    assert len(y) == 10


def test_allosteric_modulator(path_tmp):
    # Plot taken from:
    # https://en.m.wikipedia.org/wiki/File:Negative_allosteric_modulator_plot.svg
    path_out = path_tmp / "out.json"
    main(["tests/cases/unplot/plot.svg", path_out])
    with open(path_out) as fh:
        curves = json.load(fh)
    xi = curves["initial"][0]
    yi = curves["initial"][1]
    assert abs(xi[0] - 1e-2) < 1e-5
    assert abs(yi[0] - 1) < 0.1
    assert abs(xi[-1] - 2500) < 20
    assert abs(yi[-1] - 85) < 1
    assert len(xi) == 49
    assert len(yi) == 49
    xs = curves["second"][0]
    ys = curves["second"][1]
    assert abs(xs[0] - 1e-2) < 1e-5
    assert abs(ys[0] - 1) < 0.1
    assert abs(xs[-1] - 2500) < 20
    assert abs(ys[-1] - 85) < 1
    assert len(xs) == 33
    assert len(ys) == 33
    xt = curves["third"][0]
    yt = curves["third"][1]
    print(xt)
    print(yt)
    assert abs(xt[0] - 1e-2) < 1e-5
    assert abs(yt[0] - 1) < 0.1
    assert abs(xt[-1] - 2500) < 20
    assert abs(yt[-1] - 64) < 1
    assert len(xt) == 13
    assert len(yt) == 13
