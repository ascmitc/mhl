"""
__author__ = "Katharina Böttcher"
__copyright__ = "Copyright 2024, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
import pytest
from .conftest import abspath_conversion_tests
from .conftest import path_conversion_tests

from click.testing import CliRunner
from freezegun import freeze_time

import ascmhl
from ascmhl.hashlist import MHLHashList, MHLHashListReference, MHLProcessInfo
from ascmhl.history import MHLHistory


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


def test_nested_history_no_crash_when_child_has_no_ignore_patterns():
    """Bug: history.py:105 — latest_ignore_pattern_from_nested_histories iterates
    over latest_ignore_patterns() which can return None, causing TypeError."""
    parent = MHLHistory()
    parent.asc_mhl_path = "/root/ascmhl"

    child = MHLHistory()
    child.asc_mhl_path = "/root/sub/ascmhl"
    child.parent_history = parent
    # child has NO hash_lists, so latest_ignore_patterns() returns None

    parent.child_histories.append(child)
    parent.child_history_mappings["sub"] = child

    try:
        parent.latest_ignore_pattern_from_nested_histories()
    except TypeError as e:
        pytest.fail(
            f"latest_ignore_pattern_from_nested_histories crashed with TypeError: {e}. "
            f"latest_ignore_patterns() returned None for a child with no hash lists."
        )


def test_nested_history_no_crash_when_child_has_none_ignore_spec():
    """Bug: history.py:105 — same crash when child has hash lists but
    the latest has ignore_spec set to None."""
    parent = MHLHistory()
    parent.asc_mhl_path = "/root/ascmhl"

    child = MHLHistory()
    child.asc_mhl_path = "/root/sub/ascmhl"
    child.parent_history = parent

    hash_list = MHLHashList()
    hash_list.process_info = MHLProcessInfo()
    hash_list.process_info.ignore_spec = None
    child.hash_lists.append(hash_list)

    parent.child_histories.append(child)
    parent.child_history_mappings["sub"] = child

    try:
        parent.latest_ignore_pattern_from_nested_histories()
    except TypeError as e:
        pytest.fail(
            f"latest_ignore_pattern_from_nested_histories crashed with TypeError: {e}. "
            f"latest_ignore_patterns() returned None for a child with None ignore_spec."
        )


def test_resolve_references_continues_after_missing_child():
    """Bug: history.py:370 — _resolve_hash_list_references uses `return`
    instead of `continue` when a reference path is not found, aborting
    resolution of all remaining references."""
    history = MHLHistory()
    history.asc_mhl_path = "/root/ascmhl"

    # Create a child history that can be found
    child = MHLHistory()
    child.asc_mhl_path = "/root/child_b/ascmhl"
    child.parent_history = history

    child_hash_list = MHLHashList()
    child_hash_list.file_path = "/root/child_b/ascmhl/0001_child_b.mhl"
    child_hash_list.generation_number = 1
    child.hash_lists.append(child_hash_list)

    history.child_histories.append(child)
    history.child_history_mappings["child_b"] = child

    # Hash list with two references: first missing, second resolvable
    hash_list = MHLHashList()
    hash_list.file_path = "/root/ascmhl/0001_root.mhl"

    ref_missing = MHLHashListReference()
    ref_missing.path = "child_a/ascmhl/0001_child_a.mhl"
    ref_missing.reference_hash = "fake_hash_a"

    ref_found = MHLHashListReference()
    ref_found.path = "child_b/ascmhl/0001_child_b.mhl"
    child_hash_list.generate_reference_hash = lambda: "valid_hash_b"
    ref_found.reference_hash = "valid_hash_b"

    hash_list.hash_list_references.append(ref_missing)
    hash_list.hash_list_references.append(ref_found)
    history.hash_lists.append(hash_list)

    history._resolve_hash_list_references()

    assert len(hash_list.referenced_hash_lists) > 0, (
        "No references were resolved. The method returned early when it "
        "encountered the first missing reference instead of continuing."
    )
    assert child_hash_list in hash_list.referenced_hash_lists, (
        "The known child_b reference was not resolved. The method "
        "aborted at the missing child_a reference (return vs continue)."
    )
