"""
__author__ = "Jon Waggoner"
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
from lxml import etree


# TODO: determine which fixture is being used

XML_IGNORESPEC_TAG = 'ignorespec'
XML_IGNORE_TAG = 'ignore'

@pytest.fixture()
def reusable_fs(fs):
    fs.create_file('/root/B/BB/BB2.txt', contents='BB2\n')
    fs.create_file('root/a.txt', contents='a')
    fs.create_file('root/b.txt', contents='b')
    fs.create_file('root/1/c.txt', contents='c')
    fs.create_file('root/1/2/d.txt', contents='d')
    fs.create_file('root/1/2/e.txt', contents='e')
    print("FS", fs)


@pytest.fixture(scope="function")
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
    return tmpdir
    # yield tmpdir


def ignore_patterns_from_mhl_file(mhl_file):
    """
    returns a set of the patterns found in the mhl_file
    """
    pattern_list = [element.text for event, element in etree.iterparse(mhl_file) if element.tag.split('}', 1)[-1] == XML_IGNORE_TAG]
    return set(pattern_list)


def assert_mhl_file_has_exact_ignore_patterns(mhl_file: str, patterns_to_check: set):
    """
    asserts the ignore patterns in an mhl are exactly the same as the patterns in
    """
    patterns_in_file = set(ignore_patterns_from_mhl_file(mhl_file))
    assert patterns_in_file == patterns_to_check, 'mhl file has incorrect ignore patterns'


def test_ignore_on_create(temp_tree):
    """
    tests that the "create" command properly receives and processes all ignore spec arguments
    """
    runner = CliRunner()
    root_dir, mhl_dir = f'{temp_tree.path}', f'{temp_tree.path}/ascmhl'

    # write generation 1,
    runner.invoke(mhl.commands.create, [root_dir, '-i', '1'])
    # write generation 2, appending ignore patterns using both CLI args
    runner.invoke(mhl.commands.create, [root_dir, '-i', '2', '--ignore', '3'])
    # write generation 3, appending ignore_spec from file and both CLI args
    temp_tree.write('ignorespec', b'6\n7')  # write an ignore spec to file
    runner.invoke(mhl.commands.create, [root_dir, '-i', '4', '--ignore', '5', '--ignore_spec', f'{temp_tree.path}/ignorespec'])

    # we should now have 3 total mhl generations. ensure each one has exactly the expected patterns
    mhl_files = os.listdir(f'{temp_tree.path}/ascmhl')
    mhl_files.sort()
    assert_mhl_file_has_exact_ignore_patterns(f'{mhl_dir}/{mhl_files[0]}', {'.DS_Store', 'ascmhl', '1'})
    assert_mhl_file_has_exact_ignore_patterns(f'{mhl_dir}/{mhl_files[1]}', {'.DS_Store', 'ascmhl', '1', '2', '3'})
    assert_mhl_file_has_exact_ignore_patterns(f'{mhl_dir}/{mhl_files[2]}', {'.DS_Store', 'ascmhl', '1', '2', '3', '4', '5', '6', '7'})


def test_ignore_on_verify(temp_tree):
    """
    tests that the "verify" command properly receives and processes all ignore spec arguments
    """
    runner = CliRunner()
    root_dir, mhl_dir = f'{temp_tree.path}', f'{temp_tree.path}/ascmhl'

    # create a generation
    runner.invoke(mhl.commands.create, [root_dir])
    # purposely alter integrity by deleting a file
    os.remove(f'{root_dir}/a.txt')
    # assert that verification fails
    assert runner.invoke(mhl.commands.verify, [root_dir]).exit_code != 0
    # assert that we can suppress this verification error by ignoring the deleted file
    assert runner.invoke(mhl.commands.verify, [root_dir, '-i', 'a.txt']).exit_code == 0

    # again, but by ignoring a dir. alter a file, then ignore the parent.
    temp_tree.write(f'{root_dir}/1/c.txt', b'BAD_CONTENTS')
    # assert that verification fails
    assert runner.invoke(mhl.commands.verify, [root_dir]).exit_code != 0
    # assert that we can suppress this verification error by ignoring a parent directory
    assert runner.invoke(mhl.commands.verify, [root_dir, '-i', 'a.txt', '--ignore', 'c.txt']).exit_code == 0

    # assert that the same verification works by using an ignore spec from file
    temp_tree.write('ignorespec', b'a.txt\n1/c.txt')  # write an ignore spec to file
    assert runner.invoke(mhl.commands.verify, [root_dir, '--ignore_spec', f'{temp_tree.path}/ignorespec'])


def test_ignore_on_diff(temp_tree):
    """
    tests that the "diff" command properly receives and processes all ignore spec arguments
    """
    runner = CliRunner()
    root_dir, mhl_dir = f'{temp_tree.path}', f'{temp_tree.path}/ascmhl'

    # create a generation
    runner.invoke(mhl.commands.create, [root_dir])
    # purposely alter integrity by deleting a file
    os.remove(f'{root_dir}/a.txt')
    # assert that verification fails
    assert runner.invoke(mhl.commands.diff, [root_dir]).exit_code != 0
    # assert that we can suppress this verification error by ignoring the deleted file
    assert runner.invoke(mhl.commands.diff, [root_dir, '-i', 'a.txt']).exit_code == 0

    # again, but by ignoring a dir. alter a file, then ignore the parent.
    temp_tree.write(f'{root_dir}/1/c.txt', b'BAD_CONTENTS')
    # assert that verification fails
    assert runner.invoke(mhl.commands.diff, [root_dir]).exit_code != 0
    # assert that we can suppress this verification error by ignoring a parent directory
    assert runner.invoke(mhl.commands.diff, [root_dir, '-i', 'a.txt', '--ignore', '1/c.txt']).exit_code == 0

    # assert that the same verification works by using an ignore spec from file
    temp_tree.write('ignorespec', b'a.txt\n1/c.txt')  # write an ignore spec to file
    assert runner.invoke(mhl.commands.diff, [root_dir, '--ignore_spec', f'{temp_tree.path}/ignorespec'])


# def test_ignore_on_nested_histories(temp_tree):
#     """
#     tests that nested histories have proper interaction with the ignore specification
#     """
#     runner = CliRunner()
#     root_dir, mhl_dir = f'{temp_tree.path}', f'{temp_tree.path}/ascmhl'
#     child_dir = f'{root_dir}/1'
#
#     # create a generation
#     runner.invoke(mhl.commands.create, [child_dir, '-h', 'md5'])
#     runner.invoke(mhl.commands.create, [root_dir, '-h', 'c4'])
#     runner.invoke(mhl.commands.create, [child_dir, '-h', 'sha1'])
#     runner.invoke(mhl.commands.create, [root_dir, '-h', 'xxh64'])
