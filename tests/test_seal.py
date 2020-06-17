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

import mhl._debug_commands
from mhl.history_fs_backend import MHLHistoryFSBackend
import mhl.commands

scenario_output_path = 'examples/scenarios/Output'
fake_ref_path = '/ref'


@freeze_time("2020-01-16 09:15:00")
def test_seal_succeed(fs):
    fs.create_file('/root/Stuff.txt', contents='stuff\n')
    fs.create_file('/root/A/A1.txt', contents='A1\n')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root'])
    assert not result.exception
    assert os.path.exists('/root/ascmhl/root_2020-01-16_091500_0001.mhl')
    with open('/root/ascmhl/root_2020-01-16_091500_0001.mhl', 'r') as fin:
        print(fin.read())
    assert os.path.exists('/root/ascmhl/chain.txt')


def test_seal_directory_hashes(fs):
    fs.create_file('/root/Stuff.txt', contents='stuff\n')
    fs.create_file('/root/A/A1.txt', contents='A1\n')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root', '-d', '-v'])
    assert result.exit_code == 0
    assert '/root/A: d3904ee76bba3d2a' in result.output
    assert '/root: 8ac6ba5025dd1b00' in result.output

    # add some more files and folders
    fs.create_file('/root/B/B1.txt', contents='B1\n')
    fs.create_file('/root/A/A2.txt', contents='A2\n')
    fs.create_file('/root/A/AA/AA1.txt', contents='AA1\n')
    os.mkdir('/root/emptyFolderA')
    os.mkdir('/root/emptyFolderB')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root', '-d', '-v'])
    assert result.exit_code == 0
    assert '/root/A/AA: e087271288708445' in result.output
    assert '/root/A: 68bc559cd04e74df' in result.output
    assert '/root/B: aab0eba57cd1aca9' in result.output
    assert '/root/emptyFolderA: ef46db3751d8e999' in result.output
    assert '/root/emptyFolderB: ef46db3751d8e999' in result.output
    assert '/root: 65b99a36eb76e524' in result.output

    # altering the content of one file leads to a different directory hash
    with open('/root/A/A2.txt', "a") as file:
        file.write('!!')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root', '-d', '-v'])
    assert 'hash mismatch for /root/A/A2.txt' in result.output
    assert '/root/A: ed93a2f6a5a132e8' in result.output


def test_seal_fail_altered_file(fs, simple_mhl_history):
    # alter a file
    with open('/root/Stuff.txt', "a") as file:
        file.write('!!')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root'])
    assert result.exit_code == 12
    assert '/root/Stuff.txt' in result.output


def test_seal_fail_missing_file(fs, nested_mhl_histories):
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

    # the actual seal has been written to disk anyways we expect the history to contain
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
