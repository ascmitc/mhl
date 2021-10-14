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
    assert "calculated directory hash for A  xxh64: 95e230e90be29dd6 (content), 997ef53a4365b87c (structure)" in result.output
    assert "calculated root hash  xxh64: 36e824bc313f3b77 (content), 0b61ded93d2b71e6 (structure)" in result.output
    assert result.exit_code == 0

    result = runner.invoke(ascmhl.commands.verify, ["-dh", "-co", "-ro", "/root/"])
    assert "calculated directory hash for A  xxh64: 95e230e90be29dd6 (content), 997ef53a4365b87c (structure)" not in result.output
    assert "calculated root hash  xxh64: 36e824bc313f3b77 (content), 0b61ded93d2b71e6 (structure)" in result.output
    assert result.exit_code == 0
