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

scenario_output_path = "examples/scenarios/Output"
fake_ref_path = "/ref"


@freeze_time("2020-01-16 09:15:00")
def test_record_succeed_single_file(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-sf", "/root/A/A1.txt"])
    assert result.exit_code == 0
    assert os.path.exists("/root/ascmhl/0001_root_2020-01-16_091500.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")

    # make sure that only the specified file was added
    history = MHLHistory.load_from_path("/root")
    assert len(history.hash_lists[0].media_hashes) == 1
    assert history.hash_lists[0].media_hashes[0].path == "A/A1.txt"


@freeze_time("2020-01-16 09:15:00")
def test_record_succeed_single_directory(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-sf", "/root/A"])
    assert result.exit_code == 0
    assert os.path.exists("/root/ascmhl/0001_root_2020-01-16_091500.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")

    # make sure that only the specified file was added
    history = MHLHistory.load_from_path("/root")
    assert len(history.hash_lists[0].media_hashes) == 2
    assert history.hash_lists[0].media_hashes[0].path == "A/A1.txt"
    assert history.hash_lists[0].media_hashes[1].path == "A/A2.txt"


@freeze_time("2020-01-16 09:15:00")
def test_record_succeed_multiple_files(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-sf", "/root/A/A1.txt", "-sf", "/root/A/A2.txt"])
    assert result.exit_code == 0
    assert os.path.exists("/root/ascmhl/0001_root_2020-01-16_091500.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")

    # make sure that only the specified file was added
    history = MHLHistory.load_from_path("/root")
    assert len(history.hash_lists[0].media_hashes) == 2
    assert history.hash_lists[0].media_hashes[0].path == "A/A1.txt"
    assert history.hash_lists[0].media_hashes[1].path == "A/A2.txt"


def test_record_fail_altered_file(fs, simple_mhl_history):
    # alter a file
    with open("/root/Stuff.txt", "a") as file:
        file.write("!!")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-sf", "/root/Stuff.txt"])
    assert result.exit_code == 12
    assert "Stuff.txt" in result.output

    # when passing a different file to record no error ws thrown since the altered file is ignored
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-sf", "/root/A/A1.txt"])
    assert result.exit_code == 0

    # make sure we have created one failing and one succeeded generation
    history = MHLHistory.load_from_path("/root")
    assert history.hash_lists[1].media_hashes[0].path == "Stuff.txt"
    assert history.hash_lists[1].media_hashes[0].hash_entries[0].action == "failed"
    assert history.hash_lists[2].media_hashes[0].path == "A/A1.txt"
    assert history.hash_lists[2].media_hashes[0].hash_entries[0].action == "verified"
