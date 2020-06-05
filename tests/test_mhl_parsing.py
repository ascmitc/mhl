"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import pytest
import os
import time
from freezegun import freeze_time
from click.testing import CliRunner

import mhl._debug_commands
from mhl.history_fs_backend import MHLHistoryFSBackend
import mhl.commands

scenario_output_path = 'examples/scenarios/Output'
fake_ref_path = '/ref'


@pytest.fixture(scope="session", autouse=True)
def set_timezone():
    """Fakes the host timezone to UTC so we don't get different mhl files if the tests run on different time zones
    seems like freezegun can't handle timezones like we want"""
    os.environ['TZ'] = 'UTZ'
    time.tzset()


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def nested_mhl_histories(fs):

    # create mhl histories on different directly levels
    fs.create_file('/root/Stuff.txt', contents='stuff\n')
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root'])
    assert result.exit_code == 0

    fs.create_file('/root/A/AA/AA1.txt', contents='AA1\n')
    fs.create_file('/root/A/AB/AB1.txt', contents='AB1\n')
    result = runner.invoke(mhl.commands.seal, ['/root/A/AA'])
    assert result.exit_code == 0

    fs.create_file('/root/B/B1.txt', contents='B1\n')
    result = runner.invoke(mhl.commands.seal, ['/root/B'])
    assert result.exit_code == 0

    fs.create_file('/root/B/BA/BA1.txt', contents='BA1\n')
    fs.create_file('/root/B/BB/BB1.txt', contents='BB1\n')
    result = runner.invoke(mhl.commands.seal, ['/root/B/BB'])
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_child_history_parsing(fs, nested_mhl_histories):
    """

    """

    root_history = MHLHistoryFSBackend.parse('/root')
    assert len(root_history.child_histories) == 2

    aa_history = root_history.child_histories[0]
    b_history = root_history.child_histories[1]
    bb_history = root_history.child_histories[1].child_histories[0]

    assert aa_history.asc_mhl_path == '/root/A/AA/asc-mhl'
    assert aa_history.parent_history == root_history
    assert b_history.asc_mhl_path == '/root/B/asc-mhl'
    assert b_history.parent_history == root_history

    assert len(b_history.child_histories) == 1
    assert bb_history.asc_mhl_path == '/root/B/BB/asc-mhl'
    assert bb_history.parent_history == b_history

    # check sub children mappings that map all transitive children and their relative path
    assert root_history.child_history_mappings['A/AA'] == aa_history
    assert root_history.child_history_mappings['B'] == b_history
    assert root_history.child_history_mappings['B/BB'] == bb_history
    assert b_history.child_history_mappings['BB'] == bb_history

    # check if the correct (child) histories are returned for a given path
    assert root_history.find_history_for_path('Stuff.txt')[0] == root_history
    assert root_history.find_history_for_path('A/AA/AA1.txt')[0] == aa_history
    assert root_history.find_history_for_path('A/AB/AB1.txt')[0] == root_history
    assert root_history.find_history_for_path('B/B1.txt')[0] == b_history
    assert root_history.find_history_for_path('B/BA/BA1.txt')[0] == b_history
    assert root_history.find_history_for_path('B/BB/BB1.txt')[0] == bb_history

    # the history object should only return the media hashes and hash entries it contains directly
    # if we need th entries from child histories we have to ask them directly
    assert root_history.find_original_hash_entry_for_path('Stuff.txt') is not None
    assert root_history.find_original_hash_entry_for_path('A/AA/AA1.txt') is None
    assert aa_history.find_original_hash_entry_for_path('AA1.txt') is not None


@freeze_time("2020-01-16 09:15:00")
def test_child_history_verify(fs, nested_mhl_histories):
    """

    """

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root'])
    assert result.exit_code == 0

    assert os.path.isfile('/root/asc-mhl/root_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/A/AA/asc-mhl/AA_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/B/asc-mhl/B_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/B/BB/asc-mhl/BB_2020-01-16_091500_0002.ascmhl')

    root_history = MHLHistoryFSBackend.parse('/root')
    assert len(root_history.hash_lists) == 2

    assert root_history.hash_lists[1].media_hashes[0].relative_filepath == 'A/AB/AB1.txt'
    assert root_history.hash_lists[1].media_hashes[0].hash_entries[0].action == 'original'
    assert root_history.hash_lists[1].media_hashes[1].relative_filepath == 'Stuff.txt'
    assert root_history.hash_lists[1].media_hashes[1].hash_entries[0].action == 'verified'

    aa_history = root_history.child_histories[0]
    b_history = root_history.child_histories[1]
    bb_history = root_history.child_histories[1].child_histories[0]

    assert aa_history.latest_generation_number() == 2
    assert b_history.hash_lists[1].media_hashes[0].relative_filepath == 'BA/BA1.txt'
    assert b_history.hash_lists[1].media_hashes[1].relative_filepath == 'B1.txt'
    assert b_history.hash_lists[1].media_hashes[0].hash_entries[0].action == 'original'
    assert b_history.hash_lists[1].media_hashes[1].hash_entries[0].action == 'verified'

    # check that the mhl references are correct
    assert root_history.hash_lists[1].referenced_hash_lists[0] == aa_history.hash_lists[1]
    assert root_history.hash_lists[1].referenced_hash_lists[1] == b_history.hash_lists[1]
    assert b_history.hash_lists[1].referenced_hash_lists[0] == bb_history.hash_lists[1]
    assert len(aa_history.hash_lists[1].referenced_hash_lists) == 0


@freeze_time("2020-01-16 09:15:00")
def test_child_history_partial_verification_ba_1_file(fs, nested_mhl_histories):
    """

    """

    # create an additional file the verify_paths command will not add since we only pass it a single file
    fs.create_file('/root/B/B2.txt', contents='B2\n')
    runner = CliRunner()
    result = runner.invoke(mhl._debug_commands.verify_paths, ['/root', '/root/B/B1.txt'])
    assert result.exit_code == 0

    # two new generations have been written
    assert os.path.isfile('/root/asc-mhl/root_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/B/asc-mhl/B_2020-01-16_091500_0002.ascmhl')

    root_history = MHLHistoryFSBackend.parse('/root')
    assert len(root_history.hash_lists) == 2

    aa_history = root_history.child_histories[0]
    b_history = root_history.child_histories[1]
    bb_history = root_history.child_histories[1].child_histories[0]

    # the root hash list only contains a mhl reference to the hash list of the B history, no media hashes
    assert len(root_history.hash_lists[1].media_hashes) == 0
    assert root_history.hash_lists[1].referenced_hash_lists[0] == b_history.hash_lists[1]
    # the B hash list contains the media hash of the verified file
    assert b_history.hash_lists[1].media_hashes[0].relative_filepath == 'B1.txt'
    assert b_history.hash_lists[1].media_hashes[0].hash_entries[0].action == 'verified'
    # the created B2 file is not referenced in the B history, only B1
    assert len(b_history.hash_lists[1].media_hashes) == 1

    # the other histories don't have a new generation
    assert not os.path.isfile('/root/A/AA/asc-mhl/AA_2020-01-16_091500_0002.ascmhl')
    assert not os.path.isfile('/root/B/BB/asc-mhl/BB_2020-01-16_091500_0002.ascmhl')
    assert aa_history.latest_generation_number() == 1
    assert bb_history.latest_generation_number() == 1


@freeze_time("2020-01-16 09:15:00")
def test_child_history_partial_verification_bb_folder(fs, nested_mhl_histories):
    """

    """

    # create an additional file the verify_paths command will find because we pass it a folder
    fs.create_file('/root/B/BB/BB2.txt', contents='BB2\n')
    runner = CliRunner()
    result = runner.invoke(mhl._debug_commands.verify_paths, ['/root', '/root/B/BB'])
    assert result.exit_code == 0

    assert os.path.isfile('/root/asc-mhl/root_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/B/asc-mhl/B_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/B/BB/asc-mhl/BB_2020-01-16_091500_0002.ascmhl')

    root_history = MHLHistoryFSBackend.parse('/root')
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
    assert bb_history.hash_lists[1].media_hashes[0].relative_filepath == 'BB1.txt'
    assert bb_history.hash_lists[1].media_hashes[0].hash_entries[0].action == 'verified'
    assert bb_history.hash_lists[1].media_hashes[1].relative_filepath == 'BB2.txt'
    assert bb_history.hash_lists[1].media_hashes[1].hash_entries[0].action == 'original'

    # the other histories don't have a new generation
    assert not os.path.isfile('/root/A/AA/asc-mhl/AA_2020-01-16_091500_0002.ascmhl')
    assert aa_history.latest_generation_number() == 1


@freeze_time("2020-01-16 09:15:00")
def test_seal_error_missing_file(fs, nested_mhl_histories):
    """
    test that sealing fails if there is a file missing on the file system that is referenced by one of the histories
    """

    root_history = MHLHistoryFSBackend.parse('/root')
    paths = root_history.set_of_file_paths()

    assert paths == {'/root/B/B1.txt', '/root/B/BB/BB1.txt', '/root/Stuff.txt', '/root/A/AA/AA1.txt'}
    os.remove('/root/A/AA/AA1.txt')
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root'])
    assert result.exit_code == 15
    assert '/root/A/AA/AA1.txt' in result.output
    assert '1 missing files:' in result.output

    # the actual seal has been written to disk anyways we expect the history contain
    # the new not yet referenced files (/root/B/BA/BA1.txt and /root/A/AB/AB1.txt) as well now
    root_history = MHLHistoryFSBackend.parse('/root')
    paths = root_history.set_of_file_paths()

    # since we scan all generations for file paths we now get old files, missing files and new files here
    assert paths == {'/root/B/BB/BB1.txt', '/root/B/B1.txt', '/root/B/BA/BA1.txt', '/root/A/AA/AA1.txt',
                     '/root/Stuff.txt', '/root/A/AB/AB1.txt'}

    # since the file /root/A/AA/AA1.txt is still missing all further seal attempts will still fail
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root'])
    assert result.exit_code == 15
    assert '/root/A/AA/AA1.txt' in result.output
    assert '1 missing files:' in result.output