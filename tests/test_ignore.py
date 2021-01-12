"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"
__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from click.testing import CliRunner
from freezegun import freeze_time
from mhl.history import MHLHistory
from testfixtures import TempDirectory
import pytest

import mhl.commands


# @pytest.fixture(scope="module")
# def smtp_connection():
#     smtp_connection = smtplib.SMTP("smtp.gmail.com", 587, timeout=5)
#     yield smtp_connection  # provide the fixture value
#     print("teardown smtp")
#     smtp_connection.close()


# TODO: determine which fixture is being used

@pytest.fixture()
def reusable_fs(fs):
    fs.create_file('/root/B/BB/BB2.txt', contents='BB2\n')
    fs.create_file('root/a.txt', contents='a')
    fs.create_file('root/b.txt', contents='b')
    fs.create_file('root/1/c.txt', contents='c')
    fs.create_file('root/1/2/d.txt', contents='d')
    fs.create_file('root/1/2/e.txt', contents='e')
    print("FS", fs)


@pytest.fixture(scope="module")
def temp_tree():
    # TODO: flip back to with, yield
    # with TempDirectory() as tmpdir:
    tmpdir = TempDirectory()
    tmpdir.write('a.txt', b'a')
    tmpdir.write('b.txt', b'b')
    tmpdir.write('1/c.txt', b'c')
    tmpdir.write('1/11/d.txt', b'd')
    tmpdir.write('1/12/e.txt', b'e')
    tmpdir.write('2/11/f.txt', b'f')
    tmpdir.write('2/12/g.txt', b'g')
    print(f'tmpdir: {tmpdir.path}')
    return tmpdir
    # yield tmpdir


def test_ignore_propagation(temp_tree):
    """
    this test ensures that if a parent node has a generation created, the ignore specification propagates to the children.
    """
    runner = CliRunner()
    # seal child dir
    runner.invoke(mhl.commands.create, [f'{temp_tree.path}/1', '-h', 'md5'])
    # seal root dir.
    runner.invoke(mhl.commands.create, [f'{temp_tree.path}', '-i', 'd.txt', '-h', 'md5'])

    runner.invoke(mhl.commands.create, [f'{temp_tree.path}'], '-h', 'xxhash')
    # ensure second gen of child dir has parent ignore spec propagated.


def test_command_params(temp_tree):
    pass

# @freeze_time("2020-11-19 09:15:00")
# def test_simple_create_with_ignore(fs, simple_mhl_folder):
#     runner = CliRunner()
#     result = runner.invoke(mhl.commands.create, ['-i', 'Stuff.txt', '/root/'])
#     assert result.exit_code == 0
#
#     hash_list = MHLHistory.load_from_path('/root').hash_lists[-1]
#     assert hash_list.find_media_hash_for_path('Stuff.txt') is None
#     assert hash_list.find_media_hash_for_path('A/A1.txt') is not None
#
# @freeze_time("2020-11-19 09:15:00")
# def test_simple_verify_with_ignore(fs, simple_mhl_history):
#     runner = CliRunner()
#     result = runner.invoke(mhl.commands.create, ['/root/'])
#     result = runner.invoke(mhl.commands.verify, ['-i', 'Stuff.txt', '/root/'])
#     assert result.exit_code == 0
#
# @freeze_time("2020-11-19 09:15:00")
# def test_nested_create_with_ignore(fs, nested_mhl_histories):
#     runner = CliRunner()
#     result = runner.invoke(mhl.commands.create, ['-v', '-i', 'BB1.txt', '/root/'])
#     assert result.exit_code == 0
