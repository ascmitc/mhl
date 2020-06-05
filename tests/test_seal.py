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