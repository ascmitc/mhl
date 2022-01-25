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

    result = runner.invoke(ascmhl.commands.verify, ["-v", "-dh", "/root/"])
    # assert verification works before we purposefully mess things up
    assert result.exit_code == 0

    # altering the content of one file
    with open("/root/A/A2.txt", "a") as file:
        file.write("!!")

    result = runner.invoke(ascmhl.commands.verify, ["-v", "-dh", "/root/"])
    assert "ERROR: content hash mismatch" in result.output
    assert result.exit_code == 15

    # rename one file
    os.rename("/root/B/B1.txt", "/root/B/B2.txt")

    result = runner.invoke(ascmhl.commands.verify, ["-v", "-dh", "/root/"])
    assert "ERROR: structure hash mismatch" in result.output
    assert result.exit_code == 15


@freeze_time("2020-01-16 09:15:00")
def test_verify_single_file(fs, simple_mhl_history):

    runner = CliRunner()

    # verify relative path
    result = runner.invoke(ascmhl.commands.verify, ["-v", "-sf", "A/A1.txt", "/root/"])
    assert result.exit_code == 0

    # verify absolute path
    result = runner.invoke(ascmhl.commands.verify, ["-v", "-sf", "/root/A/A1.txt", "/root/"])
    assert result.exit_code == 0

    # verify existing, but not listed file
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    result = runner.invoke(ascmhl.commands.verify, ["-v", "-sf", "B/B1.txt", "/root/"])
    assert result.exit_code == 13

    # verify non existing file
    result = runner.invoke(ascmhl.commands.verify, ["-v", "-sf", "B/B2.txt", "/root/"])
    assert result.exit_code == 15

    # altering the content of one file
    with open("/root/A/A1.txt", "a") as file:
        file.write("!!")
    # verify
    result = runner.invoke(ascmhl.commands.verify, ["-v", "-sf", "A/A1.txt", "/root/"])
    assert result.exit_code == 12
