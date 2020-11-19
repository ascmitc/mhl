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

import mhl.commands

@freeze_time("2020-11-19 09:15:00")
def test_simple_create_with_ignore(fs, simple_mhl_folder):
    runner = CliRunner()
    result = runner.invoke(mhl.commands.create, ['-i', 'Stuff.txt', '/root/'])
    assert result.exit_code == 0

    hash_list = MHLHistory.load_from_path('/root').hash_lists[-1]
    assert hash_list.find_media_hash_for_path('Stuff.txt') is None
    assert hash_list.find_media_hash_for_path('A/A1.txt') is not None

@freeze_time("2020-11-19 09:15:00")
def test_simple_verify_with_ignore(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(mhl.commands.create, ['/root/'])
    result = runner.invoke(mhl.commands.verify, ['-i', 'Stuff.txt', '/root/'])
    assert result.exit_code == 0

@freeze_time("2020-11-19 09:15:00")
def test_nested_create_with_ignore(fs, nested_mhl_histories):
    runner = CliRunner()
    result = runner.invoke(mhl.commands.create, ['-v', '-i', 'BB1.txt', '/root/'])
    assert result.exit_code == 0
