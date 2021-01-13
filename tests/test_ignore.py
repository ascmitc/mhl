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
    assert patterns_in_file == patterns_to_check, 'mhl file has incorrect ignore pattern'


def test_ignore_on_create(temp_tree):
    runner = CliRunner()
    root_dir, mhl_dir = f'{temp_tree.path}', f'{temp_tree.path}/ascmhl'

    runner.invoke(mhl.commands.create, [root_dir, '-i', '1'])
    runner.invoke(mhl.commands.create, [root_dir, '-i', '2', '-i', '3'])

    temp_tree.write('ignorespec', b'6\n7')
    runner.invoke(mhl.commands.create, [root_dir, '-i', '4', '-i', '5', '--ignore_spec', f'{temp_tree.path}/ignorespec'])

    names = os.listdir(f'{temp_tree.path}/ascmhl')
    names.sort()

    assert_mhl_file_has_exact_ignore_patterns(f'{mhl_dir}/{names[0]}', {'.DS_Store', 'ascmhl', '1'})
    assert_mhl_file_has_exact_ignore_patterns(f'{mhl_dir}/{names[1]}', {'.DS_Store', 'ascmhl', '1', '2', '3'})
    assert_mhl_file_has_exact_ignore_patterns(f'{mhl_dir}/{names[2]}', {'.DS_Store', 'ascmhl', '1', '2', '3', '4', '5', '6', '7'})
