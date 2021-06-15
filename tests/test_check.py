"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from click.testing import CliRunner

import ascmhl.commands


def test_check_succeed(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert result.exit_code == 0


def test_check_fail_missing_history(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert result.exit_code == 11
    assert "/root" in result.output


def test_check_fail_altered_file(fs, simple_mhl_history):
    # alter a file
    with open("/root/Stuff.txt", "a") as file:
        file.write("!!")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert result.exit_code == 12
    assert "Stuff.txt" in result.output


def test_check_fail_new_file(fs, simple_mhl_history):
    # create a file not referenced in the history
    fs.create_file("/root/other.txt", contents="other\n")
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert result.exit_code == 13
    assert "other.txt" in result.output


def test_check_fail_missing_file(fs, simple_mhl_history):
    # remove a referenced file
    os.remove("/root/Stuff.txt")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert result.exit_code == 15
    assert "Stuff.txt" in result.output
