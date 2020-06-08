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


def test_seal_succeed(fs):
    fs.create_file('/root/Stuff.txt', contents='stuff\n')
    fs.create_file('/root/A/A1.txt', contents='A1\n')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root'])
    assert result.exit_code == 0


def test_seal_directory_hashes(fs):
    fs.create_file('/root/Stuff.txt', contents='stuff\n')
    fs.create_file('/root/A/A1.txt', contents='A1\n')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root', '-d', '-v'])
    assert result.exit_code == 0
    assert '/root/A: d3904ee76bba3d2a' in result.output
    assert '/root: 2a2892724fbdd6f5' in result.output

    # add some more files and folders
    fs.create_file('/root/B/B1.txt', contents='B1\n')
    fs.create_file('/root/A/A2.txt', contents='A2\n')
    os.mkdir('/root/emptyFolderA')
    os.mkdir('/root/emptyFolderB')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root', '-d', '-v'])
    assert result.exit_code == 0
    assert '/root/A: 5bc783e2bd1566e3' in result.output
    assert '/root/B: aab0eba57cd1aca9' in result.output
    assert '/root/emptyFolderA: ef46db3751d8e999' in result.output
    assert '/root/emptyFolderB: ef46db3751d8e999' in result.output
    assert '/root: 2a2892724fbdd6f5' in result.output

    # altering the content of one file leads to a different directory hash
    with open('/root/A/A2.txt', "a") as file:
        file.write('!!')

    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/root', '-d', '-v'])
    assert '/root/A: 72406b81dae7dd63' in result.output


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