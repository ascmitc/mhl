"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from click.testing import CliRunner
from freezegun import freeze_time

import ascmhl.commands


@freeze_time("2020-01-16 09:15:00")
def test_simple(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.verify, ["-dh", "-co", "/root/"])
    assert (
        "calculated directory hash for A  xxh64: d3904ee76bba3d2a (content), ac9bbef87384236f (structure)"
        in result.output
    )
    assert "calculated root hash  xxh64: ca56d22f064fdf1b (content), 34a27e3231744c4a (structure)" in result.output
    assert result.exit_code == 0

    result = runner.invoke(ascmhl.commands.verify, ["-dh", "-co", "-ro", "/root/"])
    assert (
        "calculated directory hash"
        not in result.output
    )
    assert "calculated root hash  xxh64: ca56d22f064fdf1b (content), 34a27e3231744c4a (structure)" in result.output
    assert result.exit_code == 0
