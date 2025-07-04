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
from .conftest import path_conversion_tests
from .conftest import abspath_conversion_tests

import ascmhl.commands


@freeze_time("2020-01-16 09:15:00")
def test_simple(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.flatten, [abspath_conversion_tests("/root"), abspath_conversion_tests("/out")]
    )
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_add_one_file_same_hashformat(fs, simple_mhl_history):
    runner = CliRunner()

    # add a sidecar
    fs.create_file("/root/sidecar.txt", contents="sidecar\n")
    runner = CliRunner()
    runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64"])

    result = runner.invoke(
        ascmhl.commands.flatten, [abspath_conversion_tests("/root"), abspath_conversion_tests("/out")]
    )
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_simple_two_hashformats(fs, simple_mhl_history):
    runner = CliRunner()

    # add a sidecar
    runner = CliRunner()
    runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "md5"])

    result = runner.invoke(
        ascmhl.commands.flatten, [abspath_conversion_tests("/root"), abspath_conversion_tests("/out")]
    )
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_nested(fs, nested_mhl_histories):
    runner = CliRunner()

    result = runner.invoke(
        ascmhl.commands.flatten, ["-v", abspath_conversion_tests("/root"), abspath_conversion_tests("/out")]
    )
    assert result.exit_code == 0

    # check for files in root and sub histories
    assert (
        result.output == f"Flattening folder at path: {abspath_conversion_tests('/root')} ...\n"
        f"  created original hash for     Stuff.txt  xxh64: 94c399c2a9a21f9a\n"
        f"\n"
        f"Child History at {path_conversion_tests('A/AA')}:\n"
        f"  created original hash for     {path_conversion_tests('A/AA/AA1.txt')}  xxh64: ab6bec9ec04704f6\n"
        f"\n"
        f"Child History at B:\n"
        f"  created original hash for     {path_conversion_tests('B/B1.txt')}  xxh64: 51fb8fb099e92821\n"
        f"\n"
        f"Child History at {path_conversion_tests('B/BB')}:\n"
        f"  created original hash for     {path_conversion_tests('B/BB/BB1.txt')}  xxh64: 5c14eac4f4ad7501\n"
        f"Created new generation {path_conversion_tests('collection_2020-01-16/packinglist_root_2020-01-16_091500Z.mhl')}\n"
    )
