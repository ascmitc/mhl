"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
import re
from freezegun import freeze_time
from click.testing import CliRunner

from ascmhl import hashlist_xml_parser
from ascmhl.__version__ import ascmhl_file_extension
from ascmhl.history import MHLHistory
import ascmhl.commands


def test_simple_parsing():
    path = "examples/scenarios/Output/scenario_01/travel_01/A002R2EC/ascmhl/0001_A002R2EC_2020-01-16_091500.mhl"
    hash_list = hashlist_xml_parser.parse(path)
    assert len(hash_list.media_hashes) > 0


@freeze_time("2020-01-16 09:15:00")
def test_child_history_parsing(fs, nested_mhl_histories):
    """ """

    root_history = MHLHistory.load_from_path("/root")
    assert len(root_history.child_histories) == 2

    aa_history = root_history.child_histories[0]
    b_history = root_history.child_histories[1]
    bb_history = root_history.child_histories[1].child_histories[0]

    assert aa_history.asc_mhl_path == "/root/A/AA/ascmhl"
    assert aa_history.parent_history == root_history
    assert b_history.asc_mhl_path == "/root/B/ascmhl"
    assert b_history.parent_history == root_history

    assert len(b_history.child_histories) == 1
    assert bb_history.asc_mhl_path == "/root/B/BB/ascmhl"
    assert bb_history.parent_history == b_history

    # check sub children mappings that map all transitive children and their relative path
    assert root_history.child_history_mappings["A/AA"] == aa_history
    assert root_history.child_history_mappings["B"] == b_history
    assert root_history.child_history_mappings["B/BB"] == bb_history
    assert b_history.child_history_mappings["BB"] == bb_history

    # check if the correct (child) histories are returned for a given path
    assert root_history.find_history_for_path("Stuff.txt")[0] == root_history
    assert root_history.find_history_for_path("A/AA/AA1.txt")[0] == aa_history
    assert root_history.find_history_for_path("A/AB/AB1.txt")[0] == root_history
    assert root_history.find_history_for_path("B/B1.txt")[0] == b_history
    assert root_history.find_history_for_path("B/BA/BA1.txt")[0] == b_history
    assert root_history.find_history_for_path("B/BB/BB1.txt")[0] == bb_history

    # the history object should only return the media hashes and hash entries it contains directly
    # if we need th entries from child histories we have to ask them directly
    assert root_history.find_original_hash_entry_for_path("Stuff.txt") is not None
    assert root_history.find_original_hash_entry_for_path("A/AA/AA1.txt") is None
    assert aa_history.find_original_hash_entry_for_path("AA1.txt") is not None


@freeze_time("2020-01-16 09:15:00")
def test_child_history_verify(fs, nested_mhl_histories):
    """ """

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root"], catch_exceptions=False)
    assert result.exit_code == 0

    assert os.path.isfile("/root/ascmhl/0002_root_2020-01-16_091500.mhl")
    assert os.path.isfile("/root/A/AA/ascmhl/0002_AA_2020-01-16_091500.mhl")
    assert os.path.isfile("/root/B/ascmhl/0002_B_2020-01-16_091500.mhl")
    assert os.path.isfile("/root/B/BB/ascmhl/0002_BB_2020-01-16_091500.mhl")

    root_history = MHLHistory.load_from_path("/root")
    assert len(root_history.hash_lists) == 2

    assert root_history.hash_lists[1].media_hashes[1].path == "A/AB/AB1.txt"
    assert root_history.hash_lists[1].media_hashes[1].hash_entries[0].action == "original"
    assert root_history.hash_lists[1].media_hashes[5].path == "Stuff.txt"
    assert root_history.hash_lists[1].media_hashes[5].hash_entries[0].action == "verified"

    aa_history = root_history.child_histories[0]
    b_history = root_history.child_histories[1]
    bb_history = root_history.child_histories[1].child_histories[0]
    root_hash_list = root_history.hash_lists[-1]
    aa_hash_list = aa_history.hash_lists[-1]
    b_hash_list = b_history.hash_lists[-1]
    bb_hash_list = bb_history.hash_lists[-1]

    assert aa_history.latest_generation_number() == 2
    assert b_hash_list.media_hashes[0].path == "BA/BA1.txt"
    assert b_hash_list.media_hashes[3].path == "B1.txt"
    assert b_hash_list.media_hashes[0].hash_entries[0].action == "original"
    assert b_hash_list.media_hashes[3].hash_entries[0].action == "verified"

    # check that the mhl references are correct
    assert root_history.hash_lists[1].referenced_hash_lists[0] == aa_hash_list
    assert root_history.hash_lists[1].referenced_hash_lists[1] == b_hash_list
    assert b_hash_list.referenced_hash_lists[0] == bb_hash_list
    assert len(aa_hash_list.referenced_hash_lists) == 0

    # the media hashes of the directories that contain a history themselves should be both in the child history
    # as root media hash and in the parent history to represent the directory that contains the child history
    aa_dir_hash = root_hash_list.find_media_hash_for_path("A/AA").hash_entries[0].hash_string
    assert aa_dir_hash
    assert aa_hash_list.process_info.root_media_hash.hash_entries[0].hash_string == aa_dir_hash
    # the dir hash of BB is in the history of B not in the root history
    assert root_hash_list.find_media_hash_for_path("B/BB") is None
    bb_dir_hash = b_hash_list.find_media_hash_for_path("BB").hash_entries[0].hash_string
    assert bb_hash_list.process_info.root_media_hash.hash_entries[0].hash_string == bb_dir_hash
    # but the dir hash of B is also in the root history
    assert root_hash_list.find_media_hash_for_path("B")


@freeze_time("2020-01-16 09:15:00")
def test_child_history_partial_verification_ba_1_file(fs, nested_mhl_histories):
    """ """

    # create an additional file the record command will not add since we only pass it B1 as single file
    fs.create_file("/root/B/B2.txt", contents="B2\n")
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-sf", "/root/B/B1.txt"], catch_exceptions=False)
    assert result.exit_code == 0

    # two new generations have been written
    assert os.path.isfile("/root/ascmhl/0002_root_2020-01-16_091500.mhl")
    assert os.path.isfile("/root/B/ascmhl/0002_B_2020-01-16_091500.mhl")

    root_history = MHLHistory.load_from_path("/root")
    assert len(root_history.hash_lists) == 2

    aa_history = root_history.child_histories[0]
    b_history = root_history.child_histories[1]
    bb_history = root_history.child_histories[1].child_histories[0]

    # the root hash list only contains a mhl reference to the hash list of the B history, no media hashes
    assert len(root_history.hash_lists[1].media_hashes) == 0
    assert root_history.hash_lists[1].referenced_hash_lists[0] == b_history.hash_lists[1]
    # the B hash list contains the media hash of the verified file
    assert b_history.hash_lists[1].media_hashes[0].path == "B1.txt"
    assert b_history.hash_lists[1].media_hashes[0].hash_entries[0].action == "verified"
    # the created B2 file is not referenced in the B history, only B1
    assert len(b_history.hash_lists[1].media_hashes) == 1

    # the other histories don't have a new generation
    assert not os.path.isfile("/root/A/AA/ascmhl/0002_AA_2020-01-16_091500.mhl")
    assert not os.path.isfile("/root/B/BB/ascmhl/0002_BB_2020-01-16_091500.mhl")
    assert aa_history.latest_generation_number() == 1
    assert bb_history.latest_generation_number() == 1


@freeze_time("2020-01-16 09:15:00")
def test_child_history_partial_verification_bb_folder(fs, nested_mhl_histories):
    """ """

    # create an additional file the record command will find because we pass it a folder
    fs.create_file("/root/B/BB/BB2.txt", contents="BB2\n")
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-sf", "/root/B/BB"])
    assert result.exit_code == 0

    assert os.path.isfile("/root/ascmhl/0002_root_2020-01-16_091500.mhl")
    assert os.path.isfile("/root/B/ascmhl/0002_B_2020-01-16_091500.mhl")
    assert os.path.isfile("/root/B/BB/ascmhl/0002_BB_2020-01-16_091500.mhl")

    root_history = MHLHistory.load_from_path("/root")
    assert len(root_history.hash_lists) == 2

    aa_history = root_history.child_histories[0]
    b_history = root_history.child_histories[1]
    bb_history = root_history.child_histories[1].child_histories[0]

    # the root and the B hash lists only contains a mhl reference to the hash list
    # down the folder hierarchy, no media hashes
    assert len(root_history.hash_lists[1].media_hashes) == 0
    assert root_history.hash_lists[1].referenced_hash_lists[0] == b_history.hash_lists[1]
    assert len(b_history.hash_lists[1].media_hashes) == 0
    assert b_history.hash_lists[1].referenced_hash_lists[0] == bb_history.hash_lists[1]

    # the BB hash list contains the media hash of the verified files in BB
    assert bb_history.hash_lists[1].media_hashes[0].path == "BB1.txt"
    assert bb_history.hash_lists[1].media_hashes[0].hash_entries[0].action == "verified"
    assert bb_history.hash_lists[1].media_hashes[1].path == "BB2.txt"
    assert bb_history.hash_lists[1].media_hashes[1].hash_entries[0].action == "original"

    # the other histories don't have a new generation
    assert not os.path.isfile("/root/A/AA/ascmhl/0002_AA_2020-01-16_091500.mhl")
    assert aa_history.latest_generation_number() == 1


def test_hash_list_name_parsing():
    def _test_regex(filename, should_match):
        filename_no_extension, _ = os.path.splitext(filename)
        if filename.endswith(ascmhl_file_extension):
            parts = re.findall(MHLHistory.history_file_name_regex, filename_no_extension)
            if should_match:
                assert len(parts) == 1 and len(parts[0]) == 2
            else:
                assert len(parts) == 0
        else:
            assert not should_match

    _test_regex("0001_AA_2020-01-16_091500.mhl", True)
    _test_regex("10001_AA_2020-01-16_091500.mhl", True)
    _test_regex("0002.mhl", True)
    _test_regex("0004_myCustomString_123.mhl", True)

    _test_regex("001_AA_2020-01-16_091500.mhl", False)
    _test_regex("0001_AA_2020-01-16_091500.xml", False)
    _test_regex("AA_2020-01-16_091500_0002.mhl", False)
    _test_regex("0003_.mhl", False)
