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
    result = runner.invoke(ascmhl.commands.flatten, ["/root/", "/out/"])
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_add_one_file_same_hashformat(fs, simple_mhl_history):
    runner = CliRunner()

    # add a sidecar
    fs.create_file("/root/sidecar.txt", contents="sidecar\n")
    runner = CliRunner()
    runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64"])

    result = runner.invoke(ascmhl.commands.flatten, ["/root/", "/out/"])
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_simple_two_hashformats(fs, simple_mhl_history):
    runner = CliRunner()

    # add a sidecar
    runner = CliRunner()
    runner.invoke(ascmhl.commands.create, ["/root", "-h", "md5"])

    result = runner.invoke(ascmhl.commands.flatten, ["/root/", "/out/"])
    assert result.exit_code == 0
