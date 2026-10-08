import os
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner
from freezegun import freeze_time

import ascmhl.commands
from ascmhl.history import MHLHistory
from .conftest import abspath_conversion_tests


@pytest.fixture
@freeze_time("2020-01-16 09:15:00")
def history_with_metadata_subdirectory(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/A/A1.txt", contents="A1\n")
    runner = CliRunner()
    for path in ("/root/B", "/root", "/A"):
        result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests(path), "-h", "xxh64"])
        assert result.exit_code == 0, result.output

    # A separate history stored inside the metadata directory must not become
    # either a generation of /root's history or a child media history.
    shutil.copytree(
        abspath_conversion_tests("/A/ascmhl"),
        abspath_conversion_tests("/root/ascmhl/A/ascmhl"),
    )


@pytest.mark.parametrize("command", [ascmhl.commands.info, ascmhl.commands.diff, ascmhl.commands.verify])
def test_metadata_subdirectory_is_excluded_with_warning(fs, history_with_metadata_subdirectory, command):
    result = CliRunner().invoke(command, [abspath_conversion_tests("/root")])

    assert result.exit_code == 0, result.output
    assert f"Warning: Ignoring subdirectory '{abspath_conversion_tests('/root/ascmhl/A')}'." in result.output
    assert "will not be loaded or verified" in result.output
    history = MHLHistory.load_from_path(abspath_conversion_tests("/root"))
    assert len(history.hash_lists) == 1
    assert set(history.child_history_mappings) == {"B"}
    assert len(history.child_histories[0].hash_lists) == 2


@freeze_time("2020-01-16 09:15:00")
def test_metadata_subdirectory_does_not_duplicate_top_level_manifest(fs, capsys):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    result = CliRunner().invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64"])
    assert result.exit_code == 0, result.output
    history = MHLHistory.load_from_path(abspath_conversion_tests("/root"))
    manifest_name = history.hash_lists[0].get_file_name()
    fs.create_dir("/root/ascmhl/A")
    shutil.copyfile(
        abspath_conversion_tests(f"/root/ascmhl/{manifest_name}"),
        abspath_conversion_tests(f"/root/ascmhl/A/{manifest_name}"),
    )

    history = MHLHistory.load_from_path(abspath_conversion_tests("/root"))

    assert len(history.hash_lists) == 1
    assert history.child_histories == []
    assert f"Warning: Ignoring subdirectory '{abspath_conversion_tests('/root/ascmhl/A')}'." in capsys.readouterr().err


@freeze_time("2020-01-16 09:15:00")
def test_create_preserves_excluded_metadata_and_valid_nested_history(fs, history_with_metadata_subdirectory):
    excluded_path = Path(abspath_conversion_tests("/root/ascmhl/A/ascmhl"))
    excluded_files = {path.name: path.read_bytes() for path in excluded_path.iterdir()}
    root_manifest = next(Path(abspath_conversion_tests("/root/ascmhl")).glob("*.mhl"))
    original_manifest = root_manifest.read_bytes()
    fs.create_file("/root/B/B2.txt", contents="B2\n")
    runner = CliRunner()

    result = runner.invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64"])

    assert result.exit_code == 0, result.output
    assert "Warning: Ignoring subdirectory" in result.output
    assert root_manifest.read_bytes() == original_manifest
    assert {path.name: path.read_bytes() for path in excluded_path.iterdir()} == excluded_files
    history = MHLHistory.load_from_path(abspath_conversion_tests("/root"))
    assert [hash_list.generation_number for hash_list in history.hash_lists] == [1, 2]
    assert set(history.child_history_mappings) == {"B"}
    child_history = history.child_history_mappings["B"]
    assert child_history.latest_generation_number() == 3
    assert child_history.hash_lists[-1].find_media_hash_for_path("B2.txt") is not None
    assert all(not path.startswith(abspath_conversion_tests("/root/ascmhl")) for path in history.set_of_file_paths())
    result = runner.invoke(ascmhl.commands.verify, [abspath_conversion_tests("/root")])
    assert result.exit_code == 0, result.output


def test_empty_metadata_subdirectory_is_reported(fs, capsys):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    result = CliRunner().invoke(ascmhl.commands.create, [abspath_conversion_tests("/root"), "-h", "xxh64"])
    assert result.exit_code == 0, result.output
    os.mkdir(abspath_conversion_tests("/root/ascmhl/emptyFolderA"))

    history = MHLHistory.load_from_path(abspath_conversion_tests("/root"))

    assert len(history.hash_lists) == 1
    assert (
        f"Warning: Ignoring subdirectory '{abspath_conversion_tests('/root/ascmhl/emptyFolderA')}'."
        in capsys.readouterr().err
    )
