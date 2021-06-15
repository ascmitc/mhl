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

import ascmhl.commands


@freeze_time("2020-01-16 09:15:00")
def test_simple_info_fails_no_history(fs, simple_mhl_history):
    runner = CliRunner()
    os.rename("/root/ascmhl", "/root/_ascmhl")
    result = runner.invoke(ascmhl.commands.info, ["-sf", "/root/Stuff.txt"])
    assert result.exit_code == 14


@freeze_time("2020-01-16 09:15:00")
def test_simple_info(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.info, ["-sf", "/root/Stuff.txt"])
    assert (
        result.output
        == "Info with history at path: /root\nStuff.txt:\n  Generation 1 (2020-01-15T13:00:00+00:00) xxh64:"
        " 94c399c2a9a21f9a (original)\n"
    )
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_info(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root/", "-h", "xxh64"])
    result = runner.invoke(ascmhl.commands.create, ["/root/", "-h", "md5"])
    result = runner.invoke(ascmhl.commands.create, ["/root/", "-h", "xxh64"])
    result = runner.invoke(ascmhl.commands.info, ["-sf", "/root/Stuff.txt"])
    assert (
        result.output
        == "Info with history at path: /root\nStuff.txt:\n  Generation 1 (2020-01-15T13:00:00+00:00) xxh64:"
        " 94c399c2a9a21f9a (original)\n  Generation 2 (2020-01-16T09:15:00+00:00) xxh64: 94c399c2a9a21f9a"
        " (verified)\n  Generation 3 (2020-01-16T09:15:00+00:00) xxh64: 94c399c2a9a21f9a (verified)\n  Generation 3"
        " (2020-01-16T09:15:00+00:00) md5: 9eb84090956c484e32cb6c08455a667b (verified)\n  Generation 4"
        " (2020-01-16T09:15:00+00:00) xxh64: 94c399c2a9a21f9a (verified)\n"
    )
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_altered_file(fs, simple_mhl_history):
    # alter a file
    with open("/root/Stuff.txt", "a") as file:
        file.write("!!")
    CliRunner().invoke(ascmhl.commands.create, ["/root"])
    CliRunner().invoke(ascmhl.commands.create, ["/root", "-h", "md5"])

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.info, ["-sf", "/root/Stuff.txt"])
    assert (
        result.output
        == "Info with history at path: /root\nStuff.txt:\n  Generation 1 (2020-01-15T13:00:00+00:00) xxh64:"
        " 94c399c2a9a21f9a (original)\n  Generation 2 (2020-01-16T09:15:00+00:00) xxh64: 2346e97eb08788cc (failed)\n"
        "  Generation 3 (2020-01-16T09:15:00+00:00) xxh64: 2346e97eb08788cc (failed)\n"
    )
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_nested_info(fs, nested_mhl_histories):
    CliRunner().invoke(ascmhl.commands.create, ["/root", "-h", "xxh64"])
    CliRunner().invoke(ascmhl.commands.create, ["/root", "-h", "md5"])

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.info, ["-sf", "/root/Stuff.txt"])
    assert (
        result.output
        == "Info with history at path: /root\nStuff.txt:\n  Generation 1 (2020-01-15T13:00:00+00:00) xxh64:"
        " 94c399c2a9a21f9a (original)\n  Generation 2 (2020-01-16T09:15:00+00:00) xxh64: 94c399c2a9a21f9a"
        " (verified)\n  Generation 3 (2020-01-16T09:15:00+00:00) xxh64: 94c399c2a9a21f9a (verified)\n  Generation 3"
        " (2020-01-16T09:15:00+00:00) md5: 9eb84090956c484e32cb6c08455a667b (verified)\n"
    )
    assert result.exit_code == 0
