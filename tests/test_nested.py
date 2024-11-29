"""
__author__ = "Katharina Böttcher"
__copyright__ = "Copyright 2024, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from .conftest import abspath_conversion_tests
from .conftest import path_conversion_tests

from click.testing import CliRunner
from freezegun import freeze_time

import ascmhl


@freeze_time("2020-01-16 09:15:00")
def test_create_nested_succeed(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")
    fs.create_file("/root/C/C1.txt", contents="A2\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")
    os.mkdir("/root/emptyFolderA")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/A/AA"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/A/AA/ascmhl/0001_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/A/AA/ascmhl/ascmhl_chain.xml")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/B"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/B/ascmhl/0001_B_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/B/ascmhl/ascmhl_chain.xml")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0001_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    with open("/root/ascmhl/0001_root_2020-01-16_091500Z.mhl", "r") as fin:
        fileContents = fin.read()
        assert "0002_AA_2020-01-16_091500Z.mhl" in fileContents
        assert "B/ascmhl/0002_B_2020-01-16_091500Z.mhl" in fileContents
        assert "AA1.txt" not in fileContents
        assert "C1.txt" in fileContents

    fs.create_file("/root/A/AA/AA2.txt", contents="AA2\n")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/A/AA/ascmhl/0003_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl")
    assert not os.path.exists("/root/ascmhl/0003_B_2020-01-16_091500Z.mhl")
    with open("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl", "r") as fin:
        fileContents = fin.read()
        assert "0003_AA_2020-01-16_091500Z.mhl" in fileContents
        assert "AA2.txt" not in fileContents

    # test history command
    result = runner.invoke(ascmhl.commands.info, [abspath_conversion_tests("/root")])
    assert f"Child History at {abspath_conversion_tests('/root/A/AA')}:" in result.output
    assert result.output.count("Generation 3") == 2
    assert result.output.count("Generation 2") == 3


@freeze_time("2020-01-16 09:15:00")
def test_create_nested_mhl_file_modified(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")
    fs.create_file("/root/C/C1.txt", contents="A2\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")
    os.mkdir("/root/emptyFolderA")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/A/AA"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/A/AA/ascmhl/0001_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/A/AA/ascmhl/ascmhl_chain.xml")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/B"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/B/ascmhl/0001_B_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/B/ascmhl/ascmhl_chain.xml")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0001_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    with open("/root/ascmhl/0001_root_2020-01-16_091500Z.mhl", "r") as fin:
        fileContents = fin.read()
        assert "0002_AA_2020-01-16_091500Z.mhl" in fileContents
        assert "B/ascmhl/0002_B_2020-01-16_091500Z.mhl" in fileContents
        assert "AA1.txt" not in fileContents
        assert "C1.txt" in fileContents

    fs.create_file("/root/A/AA/AA2.txt", contents="AA2\n")

    with open("/root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl", "a") as mhl_file:
        mhl_file.write("changed content")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert result.exception
    assert result.exit_code == 31


@freeze_time("2020-01-16 09:15:00")
def test_create_nested_mhl_file_missing(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")
    fs.create_file("/root/C/C1.txt", contents="A2\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")
    os.mkdir("/root/emptyFolderA")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/A/AA"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/A/AA/ascmhl/0001_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/A/AA/ascmhl/ascmhl_chain.xml")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/B"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/B/ascmhl/0001_B_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/B/ascmhl/ascmhl_chain.xml")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0001_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    with open("/root/ascmhl/0001_root_2020-01-16_091500Z.mhl", "r") as fin:
        fileContents = fin.read()
        assert "0002_AA_2020-01-16_091500Z.mhl" in fileContents
        assert "B/ascmhl/0002_B_2020-01-16_091500Z.mhl" in fileContents
        assert "AA1.txt" not in fileContents
        assert "C1.txt" in fileContents

    fs.create_file("/root/A/AA/AA2.txt", contents="AA2\n")

    os.remove("/root/A/AA/ascmhl/0001_AA_2020-01-16_091500Z.mhl")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert result.exception
    assert result.exit_code == 33

    result = runner.invoke(ascmhl.commands.diff, [abspath_conversion_tests("/root")])
    assert result.exception
    assert result.exit_code == 33


@freeze_time("2020-01-16 09:15:00")
def test_create_nested_mhl_chain_missing(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/A2.txt", contents="A2\n")
    fs.create_file("/root/C/C1.txt", contents="A2\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")
    os.mkdir("/root/emptyFolderA")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/A/AA"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/A/AA/ascmhl/0001_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/A/AA/ascmhl/ascmhl_chain.xml")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/B"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/B/ascmhl/0001_B_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/B/ascmhl/ascmhl_chain.xml")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0001_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    with open("/root/ascmhl/0001_root_2020-01-16_091500Z.mhl", "r") as fin:
        fileContents = fin.read()
        assert "0002_AA_2020-01-16_091500Z.mhl" in fileContents
        assert "B/ascmhl/0002_B_2020-01-16_091500Z.mhl" in fileContents
        assert "AA1.txt" not in fileContents
        assert "C1.txt" in fileContents

    fs.create_file("/root/A/AA/AA2.txt", contents="AA2\n")
    os.remove("/root/A/AA/ascmhl/ascmhl_chain.xml")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert result.exception
    assert result.exit_code == 32

    result = runner.invoke(ascmhl.commands.diff, [abspath_conversion_tests("/root")])
    assert result.exception
    assert result.exit_code == 32
