"""
__author__ = "David Frank"
__copyright__ = "Copyright 2025, Pomfort GmbH"
__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from os.path import abspath
from pathlib import Path

from click.testing import CliRunner
from freezegun import freeze_time
import ascmhl.commands
from ascmhl.generator import _extract_pattern_relative_to_history
from ascmhl.history import MHLHistory
from tests.conftest import abspath_conversion_tests, remove_tree
from tests.test_ignore import assert_mhl_file_has_exact_ignore_patterns, assert_pattern_ignored_in_result
from ascmhl.generator import belongs_to_parent_or_neighbour


@freeze_time("2020-01-16 09:15:00")
def test_ignore_relative_path_pattern_1(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "A/A1.txt", "-v"]
    )
    assert_mhl_file_has_exact_ignore_patterns("root/ascmhl/0002_root_2020-01-16_091500Z.mhl", {"/A/A1.txt"})
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/A1.txt"], result)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_relative_path_pattern_2(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "/A/A1.txt", "-v"]
    )
    assert_mhl_file_has_exact_ignore_patterns("root/ascmhl/0002_root_2020-01-16_091500Z.mhl", {"/A/A1.txt"})
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/A1.txt"], result)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_relative_path_pattern_3(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "**/A/A1.txt", "-v"]
    )
    assert_mhl_file_has_exact_ignore_patterns("root/ascmhl/0002_root_2020-01-16_091500Z.mhl", {"/**/A/A1.txt"})
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/A1.txt"], result)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_nested_path_pattern_1(fs, nested_mhl_histories):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/A"), "-h", "xxh64", "-i", "/AA/AA1.txt", "-v"]
    )
    print(result.output)
    assert_mhl_file_has_exact_ignore_patterns("root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl", {"/AA1.txt"})
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/A")).latest_ignore_patterns()
    assert "/AA/AA1.txt" not in latest_ignores

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root")).latest_ignore_patterns()
    assert "/AA/AA1.txt" not in latest_ignores


@freeze_time("2020-01-16 09:15:00")
def test_ignore_nested_path_pattern_2(fs, nested_mhl_histories):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/A"), "-h", "xxh64", "-i", "AA/AA1.txt", "-v"]
    )
    print(result.output)
    assert_mhl_file_has_exact_ignore_patterns("root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl", {"/AA1.txt"})
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/A")).latest_ignore_patterns()
    assert "AA/AA1.txt" not in latest_ignores

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root")).latest_ignore_patterns()
    assert "AA/AA1.txt" not in latest_ignores


@freeze_time("2020-01-16 09:15:00")
def test_ignore_nested_path_pattern_3(fs, nested_mhl_histories):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/A"), "-h", "xxh64", "-i", "**/AA1.txt", "-v"]
    )
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)
    assert_mhl_file_has_exact_ignore_patterns("root/A/ascmhl/0001_A_2020-01-16_091500Z.mhl", {"/**/AA1.txt"})
    assert_mhl_file_has_exact_ignore_patterns("root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl", {"/**/AA1.txt"})

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_nested_path_pattern_4(fs, nested_mhl_histories):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "AA1.txt", "-v"]
    )
    print(result.output)
    assert_mhl_file_has_exact_ignore_patterns("root/ascmhl/0002_root_2020-01-16_091500Z.mhl", {"AA1.txt"})
    assert_mhl_file_has_exact_ignore_patterns("root/A/AA/ascmhl/0002_AA_2020-01-16_091500Z.mhl", {"AA1.txt"})
    assert_mhl_file_has_exact_ignore_patterns("root/B/BB/ascmhl/0002_BB_2020-01-16_091500Z.mhl", {"AA1.txt"})
    assert_mhl_file_has_exact_ignore_patterns("root/B/ascmhl/0002_B_2020-01-16_091500Z.mhl", {"AA1.txt"})
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_nested_path_pattern_5(fs, post_house_file_structure):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/ShootingDay1"), "-h", "xxh64", "-i", "**/A/A001", "-v"]
    )
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/ShootingDay1/CameraMedia/A/A001"], result)
    assert_mhl_file_has_exact_ignore_patterns(
        "root/ShootingDay1/ascmhl/0002_ShootingDay1_2020-01-16_091500Z.mhl", {"/**/A/A001"}
    )
    assert_mhl_file_has_exact_ignore_patterns(
        "root/ShootingDay1/CameraMedia/A/ascmhl/0004_A_2020-01-16_091500Z.mhl", {"/**/A/A001"}
    )
    assert_mhl_file_has_exact_ignore_patterns(
        "root/ShootingDay1/CameraMedia/B/ascmhl/0004_B_2020-01-16_091500Z.mhl", {"/**/A/A001"}
    )


@freeze_time("2020-01-16 09:15:00")
def test_ignore_nested_path_pattern_6(fs, post_house_file_structure):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-h", "xxh64", "-i", "**/?/Proxy/", "-v"],
    )
    print(result.output)
    assert result.exit_code == 0
    pattern = ["/root/ShootingDay1/CameraMedia/A/Proxy", "/root/ShootingDay1/CameraMedia/B/Proxy"]
    assert_pattern_ignored_in_result(pattern, result)
    assert_mhl_file_has_exact_ignore_patterns(
        "root/ShootingDay1/ascmhl/0002_ShootingDay1_2020-01-16_091500Z.mhl", {"/**/?/Proxy/"}
    )
    assert_mhl_file_has_exact_ignore_patterns(
        "root/ShootingDay1/CameraMedia/A/ascmhl/0004_A_2020-01-16_091500Z.mhl", {"/**/?/Proxy/"}
    )
    assert_mhl_file_has_exact_ignore_patterns(
        "root/ShootingDay1/CameraMedia/B/ascmhl/0004_B_2020-01-16_091500Z.mhl", {"/**/?/Proxy/"}
    )


@freeze_time("2020-01-16 09:15:00")
def test_ignore_future_files(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "A/A2.txt", "-v"]
    )
    assert result.exit_code == 0

    fs.create_file("/root/A/A2.txt")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/A2.txt"], result)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_existing_files(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "A/A1.txt", "-v"]
    )
    assert_mhl_file_has_exact_ignore_patterns("root/ascmhl/0002_root_2020-01-16_091500Z.mhl", {"/A/A1.txt"})
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/A1.txt"], result)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_deleted_files(fs, simple_mhl_history):
    runner = CliRunner()
    os.remove("/root/A/A1.txt")
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "A/A1.txt", "-v"]
    )
    assert_mhl_file_has_exact_ignore_patterns("root/ascmhl/0002_root_2020-01-16_091500Z.mhl", {"/A/A1.txt"})
    print(result.output)
    assert result.exit_code == 0


@freeze_time("2020-01-16 09:15:00")
def test_ignore_changing_files(fs, simple_mhl_history):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "A/A1.txt", "-v"]
    )
    assert_mhl_file_has_exact_ignore_patterns("root/ascmhl/0002_root_2020-01-16_091500Z.mhl", {"/A/A1.txt"})
    print(result.output)

    os.remove("/root/A/A1.txt")
    fs.create_file("/root/A/A1.txt", contents="1234567890")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/A1.txt"], result)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_in_first_generation(fs):
    runner = CliRunner()

    fs.create_file("/root/A/A1.txt", contents="1234567890")
    fs.create_file("/root/A/A1.RMD", contents="1234567890")
    fs.create_file("/root/A/A2.txt", contents="1234567890")
    fs.create_file("/root/A/A2.RMD", contents="1234567890")
    fs.create_file("/root/A/ignore.ign", contents="1234567890")
    fs.create_file("/root/report.pdf", contents="1234567890")
    fs.create_file("/root/report.txt", contents="1234567890")
    fs.create_file("/root/ignore.ign", contents="1234567890")

    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root"), "-h", "xxh64", "-v", "-i", "*.txt", "-i", "ignore.ign"],
    )
    print(result.output)
    assert result.exit_code == 0
    pattern = ["/root/A/A1.txt", "/root/A/A2.txt", "/root/A/ignore.ign", "/root/ignore.ign", "/root/report.txt"]
    assert_pattern_ignored_in_result(pattern, result)
    assert_mhl_file_has_exact_ignore_patterns("root/ascmhl/0001_root_2020-01-16_091500Z.mhl", {"*.txt", "ignore.ign"})


def test_ignore_paths_are_handled_correctly(fs, nested_mhl_histories):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/A"), "-h", "xxh64", "-v", "-i", "/AB/AB1.txt"]
    )
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AB/AB1.txt"], result)

    fs.create_file("/root/AB/AB1.txt")
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v", "-i", "Stuff.txt"]
    )
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AB/AB1.txt", "/root/Stuff.txt"], result)

    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v", "-i", "A/AA/AA1.txt"]
    )
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)

    os.remove("/root/A/AA/AA1.txt")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert result.exit_code == 0

    os.remove("/root/A/AB/AB1.txt")
    os.remove("/root/Stuff.txt")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert result.exit_code == 0

    os.remove("/root/B/B1.txt")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-v"])
    assert result.exit_code == 10


def test_nested_histories_absolute_ignore_patterns(fs, nested_mhl_histories):
    runner = CliRunner()

    # existing histories: /root, /root/A/AA, /root/B, /root/B/BB (1st gen)
    # create a history with an ignore pattern
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/A/AA"), "-h", "xxh64", "-i", "/test.txt"]
    )
    assert result.exit_code == 0

    # create two test files
    fs.create_file("/root/A/AA/test.txt", contents="testAtSubHistoryRoot")
    fs.create_file("/root/A/AA/Subfolder/test.txt", contents="testInSubHistorySubfolder")

    # run the create once in the sub history and see if the ignore pattern works
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/A/AA"), "-h", "xxh64", "-v"])
    assert result.exit_code == 0
    hash_list = MHLHistory.load_from_path(abspath("/root/A/AA")).hash_lists[-1]

    # the ignore pattern /test.txt should ignore this file
    assert hash_list.find_media_hash_for_path("test.txt") is None

    # the ignore pattern /test.txt should not ignore this file
    assert hash_list.find_media_hash_for_path(f"{Path('Subfolder/test.txt')}") is not None

    # same ignores should be applied when running it on the root history, so we run it again on the root hsitory
    result = runner.invoke(ascmhl.commands.create, [abspath("/root"), "-h", "xxh64", "-v"])
    assert result.exit_code == 0
    hash_list = MHLHistory.load_from_path(abspath("/root/A/AA")).hash_lists[-1]

    # the ignore pattern /test.txt from the sub history should ignore this file also when verifying from the root
    assert hash_list.find_media_hash_for_path("test.txt") is None

    # the ignore pattern /test.txt from the sub history should not ignore this file
    assert hash_list.find_media_hash_for_path(f"{Path('Subfolder/test.txt')}") is not None


def test_nested_histories_ignoring_from_root(fs, nested_mhl_histories):
    runner = CliRunner()

    # existing histories: /root, /root/A/AA, /root/B, /root/B/BB (1st gen)
    # create two test files
    fs.create_file("/root/A/AA/test.txt", contents="testAtSubHistoryRoot")
    fs.create_file("/root/A/AA/Subfolder/test.txt", contents="testInSubHistorySubfolder")

    # ignore a file in the subhistory from the root hsitory
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64", "-i", "/A/AA/test.txt"]
    )
    assert result.exit_code == 0

    hash_list = MHLHistory.load_from_path(abspath("/root/A/AA")).hash_lists[-1]

    # the ignore pattern should ignore this file
    assert hash_list.find_media_hash_for_path("test.txt") is None

    # the ignore pattern should also ignore this file
    assert hash_list.find_media_hash_for_path(f"{Path('Subfolder/test.txt')}") is not None

    # the ignore pattern inside the sub history should contain the pattern /test.txt not the path we passed into the root history
    latest_ignores = MHLHistory.load_from_path(abspath("/root/A/AA")).latest_ignore_patterns()
    assert "/test.txt" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root")).latest_ignore_patterns()
    assert "/test.txt" not in latest_ignores

    # a second verification should not fail
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64"])
    assert result.exit_code == 0


def test_ignore_multilevel_histories(fs, nested_mhl_histories):
    runner = CliRunner()

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/A"), "-h", "xxh64"])
    assert result.exit_code == 0

    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/A/AB"), "-v", "-h", "xxh64", "-i", "AB1.txt"]
    )
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AB/AB1.txt"], result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/A/AB")).latest_ignore_patterns()
    assert "AB1.txt" in latest_ignores

    assert result.exit_code == 0
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/B/BA"), "-h", "xxh64"])
    assert result.exit_code == 0
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64"])
    assert result.exit_code == 0

    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root"), "-v", "-h", "xxh64", "-i", "/A/AA/AA1.txt"]
    )
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA1.txt"], result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/A/AA")).latest_ignore_patterns()
    assert "/AA1.txt" in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/A")).latest_ignore_patterns()
    assert "/AA/AA1.txt" not in latest_ignores
    assert "/AA1.txt" not in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/B")).latest_ignore_patterns()
    assert "/AA/AA1.txt" not in latest_ignores
    assert "/AA1.txt" not in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root")).latest_ignore_patterns()
    assert "/A/AA/AA1.txt" not in latest_ignores
    assert "/AA/AA1.txt" not in latest_ignores
    assert "/AA1.txt" not in latest_ignores


def test_ignore_files_in_nested_structures(fs, post_house_file_structure):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "Sidecar.txt", "-h", "xxh64"],
    )
    assert result.exit_code == 0

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/Sound")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores

    pattern = [
        "/root/ShootingDay1/CameraMedia/A/A001/Sidecar.txt",
        "/root/ShootingDay1/CameraMedia/B/B002/Sidecar.txt",
        "/root/ShootingDay1/Sound/Sidecar.txt",
    ]
    assert_pattern_ignored_in_result(pattern, result)


def test_ignore_file_type_in_nested_histories(fs, post_house_file_structure):
    """
    This should test the '*' functionality
    """
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root"), "-v", "-i", "*.pdf", "-h", "xxh64"],
    )
    assert result.exit_code == 0

    assert_pattern_ignored_in_result(
        ["/root/ShootingDay1/CameraMedia/Report.pdf", "/root/ShootingDay1/Report.pdf"], result
    )

    latest_ignores = MHLHistory.load_from_path(abspath("/root")).latest_ignore_patterns()
    assert "*.pdf" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "*.pdf" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/Sound")).latest_ignore_patterns()
    assert "*.pdf" in latest_ignores

    fs.create_file("/root/ShootingDay1/Sound/Notes.pdf")
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root"), "-v", "-h", "xxh64"],
    )
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/ShootingDay1/Sound/Notes.pdf"], result)


def test_ignore_file_type_in_path(fs, post_house_file_structure_with_range):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "CameraMedia/A/A002/*.mov", "-h", "xxh64"],
    )
    assert result.exit_code == 0
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "/A002/*.mov" in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/A002/A002C001.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C002.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C003.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C004.mov",
    ]
    assert_pattern_ignored_in_result(pattern, result)

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "/CameraMedia/A/A002/*.mov" not in latest_ignores
    assert "CameraMedia/A/A002/*.mov" not in latest_ignores

    # verify it again without providing the ignore pattern
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-h", "xxh64"],
    )
    assert result.exit_code == 0
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "/A002/*.mov" in latest_ignores
    assert_pattern_ignored_in_result(pattern, result)


def test_ignore_directories_in_nested_structures_pattern_1(fs, post_house_file_structure):
    """
    This pattern should match "Proxy" anywhere in the filepath
    """
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1/CameraMedia"), "-v", "-i", "Proxy", "-h", "xxh64"],
    )
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "Proxy" in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/Proxy",
        "/root/ShootingDay1/CameraMedia/B/Proxy",
        "/root/ShootingDay1/CameraMedia/Proxy",
    ]
    assert_pattern_ignored_in_result(pattern, result)
    assert result.exit_code == 0


def test_ignore_directories_in_nested_structures_pattern_2(fs, post_house_file_structure):
    """
    This pattern should only match directories named "Proxy" anywhere in the directory tree, but not files with that name
    """
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1/CameraMedia"), "-v", "-i", "Proxy/", "-h", "xxh64"],
    )
    pattern = ["/root/ShootingDay1/CameraMedia/A/Proxy", "/root/ShootingDay1/CameraMedia/B/Proxy"]
    assert_pattern_ignored_in_result(pattern, result)
    assert_pattern_ignored_in_result(["/root/ShootingDay1/CameraMedia/Proxy"], result, negate=True)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "Proxy/" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "Proxy/" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/B")).latest_ignore_patterns()
    assert "Proxy/" in latest_ignores
    assert result.exit_code == 0


def test_ignore_directories_in_nested_structures_pattern_3(fs, post_house_file_structure):
    """
    This pattern should only match /A/Proxy/ relative to CameraMedia and not be applied to other directories
    """
    runner = CliRunner()
    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/A/Proxy/B001/A3_p.txt", contents="A3 Proxy")

    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1/CameraMedia"), "-v", "-i", "A/Proxy/", "-h", "xxh64"],
    )
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "/Proxy/" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/B")).latest_ignore_patterns()
    assert "A/Proxy/" not in latest_ignores
    assert "/A/Proxy/" not in latest_ignores
    assert "//A/Proxy/" not in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "A/Proxy/" not in latest_ignores
    assert "/A/Proxy/" not in latest_ignores
    assert_pattern_ignored_in_result(["/root/ShootingDay1/CameraMedia/A/Proxy"], result)
    assert_pattern_ignored_in_result(
        ["/root/ShootingDay1/CameraMedia/B/Proxy", "/root/ShootingDay1/CameraMedia/Proxy"], result, negate=True
    )
    assert f"created original hash for     {Path('B/Proxy/A/Proxy/B001/A3_p.txt')}" in result.output
    assert result.exit_code == 0


def test_ignore_directories_in_nested_structures_pattern_3_wrong_directory(fs, post_house_file_structure):
    """
    This pattern should only match /A/Proxy/ relative to the ascmhl and not be applied to other directories
    (i.e. have no effect when called on root/ShootingDay1, since it does not contain a directory 'A/Proxy/')
    """
    runner = CliRunner()
    fs.create_file("/root/ShootingDay1/CameraMedia/B/Proxy/A/Proxy/B001/A3_p.txt", contents="A3 Proxy")

    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "A/Proxy/", "-h", "xxh64"],
    )
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "/Proxy/" not in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/B")).latest_ignore_patterns()
    assert "/A/Proxy/" not in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "/A/Proxy/" not in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/Proxy",
        "/root/ShootingDay1/CameraMedia/B/Proxy",
        "/root/ShootingDay1/CameraMedia/Proxy",
    ]
    assert_pattern_ignored_in_result(pattern, result, negate=True)
    assert f"created original hash for     {Path('CameraMedia/B/Proxy/A/Proxy/B001/A3_p.txt')}" in result.output
    assert result.exit_code == 0


def test_ignore__directories_in_nested_structures_pattern_4(fs, post_house_file_structure):
    """
    This pattern should ignore any occurence of Proxy in the file- or directoryname below root/ShootingDay1
    """
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "**/Proxy", "-h", "xxh64"],
    )
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "/**/Proxy" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "/**/Proxy" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "/**/Proxy" in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/Proxy",
        "/root/ShootingDay1/CameraMedia/B/Proxy",
        "/root/ShootingDay1/CameraMedia/Proxy",
    ]
    assert_pattern_ignored_in_result(pattern, result)
    assert result.exit_code == 0


def test_ignore__directories_in_nested_structures_pattern_5(fs, post_house_file_structure):
    """
    This pattern should ignore any directory 'Proxy', but not a file named 'Proxy'
    """
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "**/Proxy/", "-h", "xxh64"],
    )
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "/**/Proxy/" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "/**/Proxy/" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "/**/Proxy/" in latest_ignores
    pattern = ["/root/ShootingDay1/CameraMedia/A/Proxy", "/root/ShootingDay1/CameraMedia/B/Proxy"]
    assert_pattern_ignored_in_result(pattern, result)
    assert_pattern_ignored_in_result(["/root/ShootingDay1/CameraMedia/Proxy"], result, negate=True)
    assert result.exit_code == 0


def test_ignore__directories_in_nested_structures_pattern_6(fs, post_house_file_structure):
    """
    This pattern should ignore any files in any directory 'Proxy', but not a file named 'Proxy'
    """
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "**/Proxy/**", "-h", "xxh64"],
    )
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "**/Proxy/**" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "**/Proxy/**" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "**/Proxy/**" in latest_ignores
    pattern = ["/root/ShootingDay1/CameraMedia/A/Proxy", "/root/ShootingDay1/CameraMedia/B/Proxy"]
    assert_pattern_ignored_in_result(pattern, result)
    assert_pattern_ignored_in_result(["/root/ShootingDay1/CameraMedia/Proxy"], result, negate=True)
    assert result.exit_code == 0


def test_ignore_single_character(fs, post_house_file_structure_with_range):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1/CameraMedia/A"), "-v", "-i", "A002C00?.mov", "-h", "xxh64"],
    )
    assert result.exit_code == 0
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "A002C00?.mov" in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/A002/A002C001.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C002.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C003.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C004.mov",
    ]
    assert_pattern_ignored_in_result(pattern, result)


def test_ignore_single_character_in_path(fs, post_house_file_structure_with_range):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "CameraMedia/A/A002/A002C00?.mov", "-h", "xxh64"],
    )
    assert result.exit_code == 0
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "/A002/A002C00?.mov" in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/A002/A002C001.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C002.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C003.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C004.mov",
    ]
    assert_pattern_ignored_in_result(pattern, result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "CameraMedia/A/A002C00?.mov" not in latest_ignores


def test_ignore_multiple_individual_characters_in_path(fs, post_house_file_structure):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [
            abspath_conversion_tests("/root/ShootingDay1"),
            "-v",
            "-i",
            "CameraMedia/?/Proxy/?001/?001.ale",
            "-h",
            "xxh64",
        ],
    )
    assert result.exit_code == 0
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "/?/Proxy/?001/?001.ale" in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/Proxy/A001/A001.ale",
        "/root/ShootingDay1/CameraMedia/B/Proxy/B001/B001.ale",
    ]
    assert_pattern_ignored_in_result(pattern, result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "CameraMedia/?/Proxy/?001/?001.ale" not in latest_ignores


def test_ignore_range_of_characters(fs, post_house_file_structure_with_range):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [
            abspath_conversion_tests("/root/ShootingDay1"),
            "-v",
            "-i",
            "CameraMedia/A/A00[1-5]/A00?C00[1-9].mov",
            "-h",
            "xxh64",
        ],
    )
    assert result.exit_code == 0
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "/A00[1-5]/A00?C00[1-9].mov" in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/A002/A002C001.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C002.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C003.mov",
        "/root/ShootingDay1/CameraMedia/A/A002/A002C004.mov",
    ]
    assert_pattern_ignored_in_result(pattern, result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "CameraMedia/A/A00[1-5]/A00?C00[1-9].mov" not in latest_ignores


def test_ignore_negate_pattern(fs, post_house_file_structure):
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "Sidecar.txt", "-h", "xxh64"],
    )
    assert result.exit_code == 0

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/Sound")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    pattern = [
        "/root/ShootingDay1/CameraMedia/A/A001/Sidecar.txt",
        "/root/ShootingDay1/CameraMedia/B/B002/Sidecar.txt",
        "/root/ShootingDay1/Sound/Sidecar.txt",
    ]
    assert_pattern_ignored_in_result(pattern, result)
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1/Sound"), "-v", "-i", "!Sidecar.txt", "-h", "xxh64"],
    )
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/ShootingDay1/Sound/Sidecar.txt"], result, negate=True)


@freeze_time("2020-01-16 09:15:00")
def test_ignore_old_deleted_files_in_histories(fs, nested_mhl_histories):
    runner = CliRunner()

    # existing histories: /root, /root/A/AA, /root/B, /root/B/BB (1st gen)

    fs.create_file("/root/A/AA/AA1.RMD", contents="Lorem ipsum dolor")
    fs.create_file("/root/A/AB/AB1.RMD", contents="sit amet con vota")
    fs.create_file("/root/B/BA/B1.RMD", contents="lirum alamru aexti")
    fs.create_file("/root/A/AA/AA2.txt", contents="Lorem ipsum dolor")

    result = runner.invoke(ascmhl.commands.create, [abspath("/root"), "-h", "xxh64"])
    assert result.exit_code == 0
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/A/AA"), "-h", "xxh64"])
    assert result.exit_code == 0
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/B"), "-h", "xxh64"])
    assert result.exit_code == 0
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/B/BB"), "-h", "xxh64"])
    assert result.exit_code == 0

    # existing histories: /root, /root/A/AA, /root/B, /root/B/BB (2nd gen)

    print("First session, no ignores yet\n")
    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root/A"), "-h", "xxh64", "-v"])
    print(result.output)
    assert result.exit_code == 0

    print("Second Session, should ignore single existing file AB1.txt in root/A/AB/AB1.txt\n")

    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/A"), "-v", "-h", "xxh64", "-i", "AB/AB1.txt"]
    )
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AB/AB1.txt"], result)
    assert_mhl_file_has_exact_ignore_patterns("root/A/ascmhl/0002_A_2020-01-16_091500Z.mhl", {"/AB/AB1.txt"})

    print('Third Session, ignore "*.txt" and "/root/A/AB/AB1.RMD "\nRemove root/A/AA/AA1.txt and /root/A/AB/AB1.txt\n')
    os.remove("/root/A/AA/AA1.txt")
    os.remove("/root/A/AB/AB1.txt")
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/A"), "-v", "-h", "xxh64", "-i", "*.txt", "-i", "AB/AB1.RMD"],
    )
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/AA/AA2.txt", "/root/A/AB/AB1.RMD"], result)
    assert_mhl_file_has_exact_ignore_patterns(
        "root/A/ascmhl/0003_A_2020-01-16_091500Z.mhl", {"*.txt", "/AB/AB1.RMD", "/AB/AB1.txt"}
    )

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-v", "-h", "xxh64"])
    print(result.output)
    assert result.exit_code == 0

    os.remove("/root/B/BB/BB1.txt")

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-v", "-h", "xxh64"])
    print(result.output)
    assert result.exit_code == 10


def test_ignore_multiple_pattern_in_single_command(fs, post_house_file_structure):
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/Report.pdf", contents="A1")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/ClipList.pdf", contents="A1")
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [
            abspath_conversion_tests("/root/ShootingDay1"),
            "-v",
            "-h",
            "xxh64",
            "-i",
            "Sidecar.txt",
            "-i",
            "Proxy/",
            "-i",
            "CameraMedia/**/*.pdf",
            "-i",
            "/CameraMedia/B/B002/B3.txt",
        ],
    )
    assert result.exit_code == 0

    pattern = [
        "/root/ShootingDay1/CameraMedia/Report.pdf",
        "/root/ShootingDay1/CameraMedia/A/A001/Report.pdf",
        "/root/ShootingDay1/CameraMedia/B/B002/ClipList.pdf",
        "/root/ShootingDay1/CameraMedia/B/B002/Sidecar.txt",
        "/root/ShootingDay1/Sound/Sidecar.txt",
        "/root/ShootingDay1/CameraMedia/A/Proxy",
        "/root/ShootingDay1/CameraMedia/B/Proxy",
    ]
    assert_pattern_ignored_in_result(pattern, result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "Proxy/" in latest_ignores
    assert "/CameraMedia/**/*.pdf" not in latest_ignores
    assert "/CameraMedia/B/B002/B3.txt" not in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/Sound")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "Proxy/" in latest_ignores
    assert "CameraMedia/**/*.pdf" not in latest_ignores
    assert "/CameraMedia/B/B002/B3.txt" not in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "Proxy/" in latest_ignores
    assert "/**/*.pdf" in latest_ignores
    assert "/CameraMedia/B/B002/B3.txt" not in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "Proxy/" in latest_ignores
    assert "/**/*.pdf" in latest_ignores
    assert "/B002/B3.txt" not in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/B")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "Proxy/" in latest_ignores
    assert "/**/*.pdf" in latest_ignores
    assert "/B002/B3.txt" in latest_ignores


def test_ignore_diff_nested_multiple_pattern(fs, post_house_file_structure):
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/Report.pdf", contents="A1")
    fs.create_file("/root/ShootingDay1/CameraMedia/B/B002/ClipList.pdf", contents="A1")
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.diff,
        [
            abspath_conversion_tests("/root/ShootingDay1"),
            "-v",
            "-i",
            "Sidecar.txt",
            "-i",
            "Proxy/",
            "-i",
            "CameraMedia/**/*.pdf",
            "-i",
            "/CameraMedia/B/B002/B3.txt",
            "-i",
            "/CameraMedia/Proxy",
        ],
    )
    assert result.exit_code == 0

    pattern = [
        "/root/ShootingDay1/CameraMedia/Report.pdf",
        "/root/ShootingDay1/CameraMedia/A/A001/Report.pdf",
        "/root/ShootingDay1/CameraMedia/B/B002/ClipList.pdf",
        "/root/ShootingDay1/CameraMedia/B/B002/Sidecar.txt",
        "/root/ShootingDay1/Sound/Sidecar.txt",
        "/root/ShootingDay1/CameraMedia/A/Proxy",
        "/root/ShootingDay1/CameraMedia/B/Proxy",
    ]
    assert_pattern_ignored_in_result(pattern, result)


def test_ignore_from_file(fs, post_house_file_structure):
    fs.create_file(
        "/user/ignore.txt", contents="Sidecar.txt\n/CameraMedia/**/Proxy/**\nCameraMedia/A/A001/A1.txt\n/**/temp\n/dir"
    )

    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-h", "xxh64", "-ii", "/user/ignore.txt"],
    )
    assert result.exit_code == 0

    pattern = [
        "/root/ShootingDay1/CameraMedia/A/A001/A1.txt",
        "/root/ShootingDay1/CameraMedia/A/A001/Sidecar.txt",
        "/root/ShootingDay1/CameraMedia/B/B002/Sidecar.txt",
        "/root/ShootingDay1/CameraMedia/A/Proxy",
        "/root/ShootingDay1/CameraMedia/B/Proxy",
        "/root/ShootingDay1/Sound/Sidecar.txt",
    ]
    assert_pattern_ignored_in_result(pattern, result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/A")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "/A001/A1.txt" in latest_ignores
    assert "/**/temp" in latest_ignores
    assert "/dir" not in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia/B")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "/A001/A1.txt" not in latest_ignores
    assert "/**/temp" in latest_ignores
    assert "/dir" not in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "/**/Proxy/**" in latest_ignores
    assert "/A001/A1.txt" not in latest_ignores
    assert "/**/temp" in latest_ignores
    assert "/dir" not in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/Sound")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "/CameraMedia/**/Proxy/**" not in latest_ignores
    assert "/CameraMedia/A001/A1.txt" not in latest_ignores
    assert "/**/temp" in latest_ignores
    assert "/dir" not in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "Sidecar.txt" in latest_ignores
    assert "/CameraMedia/**/Proxy/**" not in latest_ignores
    assert "/CameraMedia/A001/A1.txt" not in latest_ignores
    assert "/**/temp" in latest_ignores
    assert "/dir" in latest_ignores


def test_ignore_history_in_ignored_directory(fs):
    runner = CliRunner()
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A1.txt", contents="A1")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A2.txt", contents="A2")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/A3.txt", contents="A3")
    fs.create_file("/root/ShootingDay1/CameraMedia/A/A001/Sidecar.txt", contents="Sidecar1")
    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1"), "-h", "xxh64"])
    assert result.exit_code == 0

    result = runner.invoke(ascmhl.commands.create, [abspath("/root/ShootingDay1/CameraMedia"), "-h", "xxh64"])
    assert result.exit_code == 0

    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1/CameraMedia/A/A001"), "-v", "-h", "xxh64"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-i", "/CameraMedia/A/A001", "-h", "xxh64"],
    )
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/ShootingDay1/CameraMedia/A/A001"], result)
    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1/CameraMedia")).latest_ignore_patterns()
    assert "/A/A001" in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/ShootingDay1")).latest_ignore_patterns()
    assert "/CameraMedia/A/A001" not in latest_ignores

    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/ShootingDay1"), "-v", "-h", "xxh64"],
    )
    print(result.output)
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/ShootingDay1/CameraMedia/A/A001"], result)


def test_ignore_only_one_child_history(fs):
    fs.create_file("/root/A/A001/A001C001.txt")
    fs.create_file("/root/A/A001/A001C002.txt")
    fs.create_file("/root/A/A001/A001C003.txt")

    fs.create_file("/root/A/A002/A002C001.txt")
    fs.create_file("/root/A/A002/A002C002.txt")
    fs.create_file("/root/A/A002/A002C003.txt")

    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/A/A002"), "-v", "-h", "xxh64"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        ascmhl.commands.create,
        [abspath_conversion_tests("/root/A"), "-v", "-i", "/A001/A001C001.txt", "-h", "xxh64"],
    )
    assert result.exit_code == 0
    assert_pattern_ignored_in_result(["/root/A/A001/A001C001.txt"], result)

    latest_ignores = MHLHistory.load_from_path(abspath("/root/A")).latest_ignore_patterns()
    assert "/A001/A001C001.txt" in latest_ignores

    latest_ignores = MHLHistory.load_from_path(abspath("/root/A/A002")).latest_ignore_patterns()
    assert "/A001/A001C001.txt" not in latest_ignores


def test_ignore_unit_belongs_to_parent_or_neighbour():
    pattern = "*.txt"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == False

    pattern = "A.txt"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == False

    pattern = "A/"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == False

    pattern = "/A"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "/A/"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "/A/AA"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "/A/AA/"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "/A/AA/AAA"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "/A/AA/AAA.txt"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "/A/AA/AAA/A.txt"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == False

    pattern = "A/**/AA"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == False

    pattern = "A/AA/**"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "**/AA/"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == False

    pattern = "/**/AA"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "/**/AA/"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "A/B/AAA"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "A/AA/AAB"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "A/AA/AAB/AA"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "B/AA/AAA"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True

    pattern = "/B/AA/AAA"
    parent_rel_path = f"{Path('/A/AA/AAA')}"
    result = ascmhl.generator.belongs_to_parent_or_neighbour(pattern, parent_rel_path)
    assert result == True


def test_ignore_unit_extract_relpath():
    base = f"{Path('/home/user/docs')}"
    target = "/home/user/docs/file.txt"
    expected = "file.txt"
    result = ascmhl.generator._extract_pattern_relative_to_history(target, base)
    assert result == expected

    base = f"{Path('/home/user')}"
    target = "/home/user/projects/code"
    expected = "projects/code"
    result = ascmhl.generator._extract_pattern_relative_to_history(target, base)
    assert result == expected

    base = f"{Path('/home/user/docs')}"
    target = "/home/user"
    expected = None
    result = ascmhl.generator._extract_pattern_relative_to_history(target, base)
    assert result == expected

    base = f"{Path('/home/user/docs')}"
    target = "/home/user/photos/image.jpg"
    expected = "photos/image.jpg"
    result = ascmhl.generator._extract_pattern_relative_to_history(target, base)
    assert result == expected

    base = f"{Path('/home/user/docs')}"
    target = "/home/user/docs"
    expected = None
    result = ascmhl.generator._extract_pattern_relative_to_history(target, base)
    assert result == expected

    base = f"{Path('/')}"
    target = "/var/log"
    expected = "var/log"
    result = ascmhl.generator._extract_pattern_relative_to_history(target, base)
    assert result == expected

    base = f"{Path('/home/user')}"
    target = "/home/user/docs/"
    expected = "docs/"
    result = ascmhl.generator._extract_pattern_relative_to_history(target, base)
    assert result == expected


def test_ignore_missing_subhistory(fs, post_house_file_structure):
    """
    test that creating a new generation doesn't fail if we ignore a missing subhistory
    """

    # delete the whole subhistory, it is referenced from the history in the CameraMedia folder but as we ignore it
    # the create command doesn't fail
    remove_tree("/root/ShootingDay1/CameraMedia/A")
    runner = CliRunner()
    result = runner.invoke(
        ascmhl.commands.create, [abspath_conversion_tests("/root/ShootingDay1/CameraMedia"), "-i", "/A"]
    )
    assert result.exit_code == 0
