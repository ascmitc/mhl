import pytest
import os
import time
from freezegun import freeze_time
from click.testing import CliRunner
from src import verify
from src.mhllib.mhl_history_xml_backend import MHLHistoryXMLBackend

scenario_output_path = '../Scenarios/Output'
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
    result = runner.invoke(verify, ['/root'])
    assert result.exit_code == 0

    fs.create_file('/root/A/AA/AA1.txt', contents='AA1\n')
    fs.create_file('/root/A/AB/AB1.txt', contents='AB1\n')
    result = runner.invoke(verify, ['/root/A/AA'])
    assert result.exit_code == 0

    fs.create_file('/root/B/B1.txt', contents='B1\n')
    result = runner.invoke(verify, ['/root/B'])
    assert result.exit_code == 0

    fs.create_file('/root/B/BA/BA1.txt', contents='BA1\n')
    fs.create_file('/root/B/BB/BB1.txt', contents='BB1\n')
    result = runner.invoke(verify, ['/root/B/BB'])
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_child_history_parsing(fs, nested_mhl_histories):
    """

    """

    root_history = MHLHistoryXMLBackend.parse('/root')
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
    assert root_history.find_history_for_path('A/AB/AB1.txt')[0] is root_history
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
    result = runner.invoke(verify, ['/root'])
    assert result.exit_code == 0

    assert os.path.isfile('/root/asc-mhl/root_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/A/AA/asc-mhl/AA_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/B/asc-mhl/B_2020-01-16_091500_0002.ascmhl')
    assert os.path.isfile('/root/B/BB/asc-mhl/BB_2020-01-16_091500_0002.ascmhl')

    root_history = MHLHistoryXMLBackend.parse('/root')
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



