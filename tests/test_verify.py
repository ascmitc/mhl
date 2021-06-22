"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from freezegun import freeze_time
from click.testing import CliRunner

from ascmhl.history import MHLHistory
import ascmhl.commands


@freeze_time("2020-01-16 09:15:00")
def test_simple_verify_fails_no_history(fs, simple_mhl_history):
    runner = CliRunner()
    os.rename("/root/ascmhl", "/root/_ascmhl")
    result = runner.invoke(ascmhl.commands.verify, ["-v", "/root/Stuff.txt"])
    assert result.exit_code == 11


@freeze_time("2020-01-16 09:15:00")
def test_simple_verify(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.verify, ["-v", "/root/"])
    assert (
        result.output
        == "check folder at path: /root/\nverification (xxh64) of file A/A1.txt: OK\nverification (xxh64) of file"
        " Stuff.txt: OK\n"
    )
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_directory_verify(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.verify, ["-v", "-dh", "/root/"])
    assert "verification of root folder   OK (generation 0001)\n" in result.output
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_directory_verify_detect_changes(fs, simple_mhl_history):

    # add some more files and folders
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")
    os.mkdir("/root/emptyFolderA")
    os.mkdir("/root/emptyFolderB")
    os.mkdir("/root/emptyFolderC")
    os.mkdir("/root/emptyFolderC/emptyFolderCA")
    os.mkdir("/root/emptyFolderC/emptyFolderCB")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-v"])
    assert result.exit_code == 0

    # altering the content of one file
    with open("/root/A/A2.txt", "a") as file:
        file.write("!!")

    result = runner.invoke(ascmhl.commands.verify, ["-v", "-dh", "/root/"])
    assert (
        "ERROR: content hash mismatch   for A old xxh128: 4c8e69c311b21a0a1b3e54fac069fdab, new xxh128:"
        " 26f0b33a4f7de085f5128d6972ced366 (generation 0002)"
        in result.output
    )
    assert result.exit_code == 15

    # rename one file
    os.rename("/root/B/B1.txt", "/root/B/B2.txt")

    result = runner.invoke(ascmhl.commands.verify, ["-v", "-dh", "/root/"])
    assert (
        "ERROR: structure hash mismatch for B old xxh128: c523dc4f6078c7617bf958873544aab6, new xxh128:"
        " 5c3a07fb32c5180f763d29d762f5c746 (generation 0002)"
        in result.output
    )
    assert result.exit_code == 15
