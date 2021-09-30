"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""
import difflib
import filecmp
import glob
import os
import shutil
from importlib import reload
from typing import List

import pytest
from click.testing import CliRunner
from freezegun import freeze_time
from pyfakefs.fake_filesystem_unittest import Pause

import ascmhl.commands

scenario_output_path = "examples/scenarios/Output"
fake_ref_root_path = "/ref"


@pytest.fixture(autouse=True)
def version(monkeypatch):
    monkeypatch.setattr("ascmhl.__version__.ascmhl_tool_version", "0.3 alpha")
    monkeypatch.setattr("ascmhl.__version__.ascmhl_tool_name", "ascmhl.py")
    reload(ascmhl.commands)


@pytest.fixture()
def reference(fs):
    load_real_reference(fs)


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def card_a002(fs):
    fs.create_file("/A002R2EC/Sidecar.txt", contents="BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n")
    fs.create_file("/A002R2EC/Clips/A002C006_141024_R2EC.mov", contents="abcd\n")
    fs.create_file("/A002R2EC/Clips/A002C007_141024_R2EC.mov", contents="def\n")


@pytest.fixture
@freeze_time("2020-01-15 13:30:00")
def card_a003(fs):
    fs.create_file("/A003R2EC/Sidecar.txt", contents="Dolor sit amet, consetetur sadipscing elitr.\n")
    fs.create_file("/A003R2EC/Clips/A003C011_141024_R2EC.mov", contents="vbgh\n")
    fs.create_file("/A003R2EC/Clips/A003C012_141024_R2EC.mov", contents="zhgdr\n")


def load_real_reference(fake_fs):
    fake_fs.add_real_directory(scenario_output_path, target_path=fake_ref_root_path)


# custom dircmp to compare file contents as suggested in https://stackoverflow.com/a/24860799
class ContentDircmp(filecmp.dircmp):
    """
    Compare the content of dir1 and dir2. In contrast with filecmp.dircmp, this
    subclass compares the content of files with the same path.
    """

    # noinspection PyAttributeOutsideInit
    def phase3(self):
        """
        Find out differences between common files.
        Ensure we are using content comparison with shallow=False.
        """
        fcomp = filecmp.cmpfiles(self.left, self.right, self.common_files, shallow=False)
        self.same_files, self.diff_files, self.funny_files = fcomp


def dirs_are_equal(dir1, dir2):
    """
    Compare two directory trees content.
    Return False if they differ, True is they are the same.
    """
    result = True
    compared = ContentDircmp(dir1, dir2, ignore=[".DS_Store"])
    if compared.left_only or compared.right_only or compared.diff_files or compared.funny_files:
        compared.report_partial_closure()
        for file in compared.diff_files:
            print_diff_of_files(os.path.join(dir1, file), os.path.join(dir2, file))
        result = False
    for subdir in compared.common_dirs:
        if not dirs_are_equal(os.path.join(dir1, subdir), os.path.join(dir2, subdir)):
            result = False
    return result


def compare_dir_content(reference: str, dir_path: str) -> bool:
    if os.path.isabs(dir_path):
        relative_path = dir_path.lstrip(os.sep)
    else:
        relative_path = dir_path
    ref_path = os.path.join(fake_ref_root_path, reference, relative_path)
    if os.path.isdir(dir_path) is True and os.path.isdir(ref_path) is True:
        result = dirs_are_equal(ref_path, dir_path)
    else:
        result = False

    return result


def compare_file_content(reference: str, path: str) -> bool:
    if os.path.isabs(path):
        relative_path = path.lstrip(os.sep)
    else:
        relative_path = path
    ref_path = os.path.join(fake_ref_root_path, reference, relative_path)
    if os.path.isfile(path) is True and os.path.isfile(ref_path) is True:
        result = filecmp.cmp(ref_path, path, shallow=False)
        if result is not True:
            print("\ngot different files:\n")
            print_diff_of_files(ref_path, path)
    else:
        result = False
    return result


def print_diff_of_files(path_a: str, path_b: str):
    with open(path_a, "r") as file:
        data_a = file.readlines()
    with open(path_b, "r") as file:
        data_b = file.readlines()
    diff = difflib.unified_diff(data_a, data_b, fromfile=path_a, tofile=path_b, n=2, lineterm="")
    for line in diff:
        print(line.rstrip())


def compare_files_against_reference(scenario_reference: str, folder_paths: List[str], fake_fs) -> bool:
    """
    checks if the scenario reference folder exists in the output folder if it doesn't we copy the folders there and
    consider it as reference. This way we can easily recreate the reference files of a scenario by deleting it on disk
    and running the tests
    """
    real_ref_path = os.path.join(scenario_output_path, scenario_reference)

    with Pause(fake_fs):
        if os.path.isdir(real_ref_path):
            # in case the reference path exists we compare the content
            compare_mode = True
        else:
            # otherwise we just write the result to the output folder
            # to be used as new reference for the next run
            compare_mode = False

    result = True
    for folder_path in folder_paths:
        validate_all_mhl_files_against_xml_schema(folder_path)
        assert os.path.isabs(folder_path)
        if compare_mode:
            result &= compare_dir_content(scenario_reference, folder_path)
        else:
            copy_fake_directory_to_real_fs(folder_path, real_ref_path, fake_fs)
            # also copy the log file
            with open("/log.txt", "rb") as file:
                data = file.read()
            with Pause(fake_fs):
                with open(os.path.join(real_ref_path, "log.txt"), "w+b") as dst_file:
                    dst_file.write(data)

    if compare_mode:
        # we always assume a log.txt to exists for each scenario, compare it as well to check differences in tool output
        result &= compare_file_content(scenario_reference, "/log.txt")
    return result


def validate_all_mhl_files_against_xml_schema(folder_path: str):
    """Find all mhl files created and validate them against the xsd"""
    mhl_files = glob.glob(folder_path + r"/**/*.mhl", recursive=True)
    runner = CliRunner()
    for file in mhl_files:
        result = runner.invoke(ascmhl.commands.xsd_schema_check, file)
        assert result.exit_code == 0, result.output


def copy_fake_directory_to_real_fs(fake_dir: str, real_dir: str, fake_fs):
    """Utility function to copy a directory in the fake file system recursively to the real file system"""
    for root, _, file_names in os.walk(fake_dir):
        relative_root = root.lstrip(os.sep)
        current_real_dir = os.path.join(real_dir, relative_root)
        with Pause(fake_fs):
            os.makedirs(current_real_dir)
        for file_name in file_names:
            with open(os.path.join(root, file_name), "rb") as file:
                data = file.read()
            with Pause(fake_fs):
                with open(os.path.join(current_real_dir, file_name), "w+b") as dst_file:
                    dst_file.write(data)


def log_message(message: str):
    log_path = "/log.txt"
    with open(log_path, "a") as file:
        file.write(message)
        file.write("\n")


def execute_command(click_cmd, args):
    runner = CliRunner()
    log_message("")
    log_message(f'$ ascmhl.py {click_cmd.name} {" ".join(args)}')
    result = runner.invoke(click_cmd, args)
    log_message(result.output)
    log_message("")
    return result


@freeze_time("2020-01-16 09:15:00")
def test_scenario_01(fs, reference, card_a002):
    log_message("Scenario 01:")
    log_message("This is the most basic example. A camera card is copied to a travel drive and an ASC-MHL file is")
    log_message("created with hashes of all files on the card.")
    log_message("")

    log_message("Assume the source card /A002R2EC is copied to a travel drive /travel_01.")
    shutil.copytree("/A002R2EC", "/travel_01/A002R2EC")

    log_message("")
    log_message("Seal the copy on the travel drive /travel_01 to create the original mhl generation.")
    result = execute_command(ascmhl.commands.create, ["-v", "/travel_01/A002R2EC", "-h", "xxh64"])
    assert result.exit_code == 0
    assert compare_files_against_reference("scenario_01", ["/travel_01"], fs)


@freeze_time("2020-01-16 09:15:00")
def test_scenario_02(fs, reference, card_a002):
    log_message("Scenario 02:")
    log_message("In this scenario a copy is made, and then a copy of the copy. Two ASC-MHL are created during")
    log_message("this process, documenting the history of both copy processes.")
    log_message("")

    log_message("Assume the source card /A002R2EC is copied to a travel drive /travel_01.")
    shutil.copytree("/A002R2EC", "/travel_01/A002R2EC")

    log_message("")
    log_message("Seal the copy on the travel drive /travel_01 to create the original mhl generation.")
    result = execute_command(ascmhl.commands.create, ["-v", "/travel_01/A002R2EC", "-h", "xxh64"])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        log_message("")
        log_message("Assume the travel drive arrives at a facility on the next day.")
        log_message("And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.")
        shutil.copytree("/travel_01/A002R2EC", "/file_server/A002R2EC")

        log_message("")
        log_message("Creating new generation for the folder A002R2EC again on the file server")
        log_message("this will verify all hashes, check for completeness and create a second generation")
        result = execute_command(ascmhl.commands.create, ["-v", "/file_server/A002R2EC", "-h", "xxh64"])
        assert result.exit_code == 0
        assert compare_files_against_reference("scenario_02", ["/travel_01", "/file_server"], fs)


@freeze_time("2020-01-16 09:15:00")
def test_scenario_03(fs, reference, card_a002):
    log_message("Scenario 03:")
    log_message("In this scenario the first hashes are created using the xxhash format. Different hash formats")
    log_message("might be required by systems used further down the workflow, so the second copy is verified")
    log_message("against the existing xxhash hashes, and additional MD5 hashes can be created and stored during")
    log_message("that process on demand.")
    log_message("")

    log_message("Assume the source card /A002R2EC is copied to a travel drive /travel_01.")
    shutil.copytree("/A002R2EC", "/travel_01/A002R2EC")

    log_message("")
    log_message("Seal the copy on the travel drive /travel_01 to create the original mhl generation.")
    result = execute_command(ascmhl.commands.create, ["-v", "/travel_01/A002R2EC", "-h", "xxh64"])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        log_message("")
        log_message("Assume the travel drive arrives at a facility on the next day.")
        log_message("And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.")
        shutil.copytree("/travel_01/A002R2EC", "/file_server/A002R2EC")

        log_message("")
        log_message("Creating new generation for the folder A002R2EC again on the file server using MD5 hash format")
        log_message("this will verify all existing xxHashes, check for completeness,")
        log_message("and create a second generation with additional (new) MD5 hashes.")
        result = execute_command(ascmhl.commands.create, ["-v", "-h", "md5", "/file_server/A002R2EC"])
        assert result.exit_code == 0
        assert compare_files_against_reference("scenario_03", ["/travel_01", "/file_server"], fs)


@freeze_time("2020-01-16 09:15:00")
def test_scenario_04(fs, reference, card_a002):
    log_message("Scenario 04:")
    log_message("Copying a folder to a travel drive and from there to a file server with a hash mismatch in")
    log_message("one file.")
    log_message("")

    log_message("Assume the source card /A002R2EC is copied to a travel drive /travel_01.")
    shutil.copytree("/A002R2EC", "/travel_01/A002R2EC")

    log_message("")
    log_message("Seal the copy on the travel drive /travel_01 to create the original mhl generation.")
    result = execute_command(ascmhl.commands.create, ["-v", "/travel_01/A002R2EC", "-h", "xxh64"])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        log_message("")
        log_message("Assume the travel drive arrives at a facility on the next day.")
        log_message("And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.")
        shutil.copytree("/travel_01/A002R2EC", "/file_server/A002R2EC")

        log_message("")
        log_message("afterwards we simulate that during the copy the Sidecar.txt got corrupt (altered")
        log_message("by modifying the file content")
        with open("/file_server/A002R2EC/Sidecar.txt", "a") as file:
            file.write("!!")

        log_message("")
        log_message("Creating new generation for the folder A002R2EC again on the file server.")
        log_message("This will verify all existing hashes and fail because Sidecar.txt was altered.")
        log_message("An error is shown and create a new generation that documents the failed verification")
        result = execute_command(ascmhl.commands.create, ["-v", "/file_server/A002R2EC", "-h", "xxh64"])
        assert result.exit_code == 12
        assert compare_files_against_reference("scenario_04", ["/travel_01", "/file_server"], fs)

        # the second generation will include the failed verification result


@freeze_time("2020-01-16 09:15:00")
def test_scenario_05(fs, reference, card_a002, card_a003):
    log_message("Scenario 05:")
    log_message("Copying two camera mags to a `Reels` folder on a travel drive, and the entire `Reels` folder")
    log_message("folder to a server.")
    log_message("")

    os.makedirs("/travel_01/Reels")
    os.makedirs("/file_server")

    log_message("Assume the source card /A002R2EC is copied to a Reels folder on travel drive /travel_01.")
    shutil.copytree("/A002R2EC", "/travel_01/Reels/A002R2EC")

    log_message("")
    log_message("Seal the copy of A002R2EC on the travel drive /travel_01 to create the original mhl generation.")
    result = execute_command(ascmhl.commands.create, ["-v", "/travel_01/Reels/A002R2EC", "-h", "xxh64"])
    assert result.exit_code == 0

    log_message("")
    log_message("Assume a second card /A003R2EC is copied to the same Reels folder on travel drive /travel_01.")
    shutil.copytree("/A003R2EC", "/travel_01/Reels/A003R2EC")

    log_message("")
    log_message("Seal the copy of A003R2EC on the travel drive /travel_01 to create the original mhl generation.")
    result = execute_command(ascmhl.commands.create, ["-v", "/travel_01/Reels/A003R2EC", "-h", "xxh64"])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        log_message("")
        log_message("Assume the travel drive arrives at a facility on the next day.")
        log_message("And the common Reels folder is copied from the travel drive to a file server at /file_server.")
        shutil.copytree("/travel_01/Reels", "/file_server/Reels")

        log_message("")
        log_message("Afterwards an arbitrary file Summary.txt is added to the Reels folder.")
        # An arbitrary file `Summary.txt` is added to the `Reels` folder.
        fs.create_file(
            "/file_server/Reels/Summary.txt", contents="This is a random summary\n\n* A002R2EC\n* A003R2EC\n"
        )

        log_message("")
        log_message("Creating new generation for the Reels folder on the file server.")
        log_message("This will verify all hashes, check for completeness and create two second generations")
        log_message("in the card sub folders A002R2EC and A003R2EC and an initial one for the Reels folder")
        log_message("with the original hash of the Summary.txt and references to the child histories")
        log_message("of the card sub folders.")
        # The `Reels` folder is verified on the file server.
        result = execute_command(ascmhl.commands.create, ["-v", "/file_server/Reels", "-h", "xxh64"])
        assert result.exit_code == 0
        assert compare_files_against_reference("scenario_05", ["/travel_01", "/file_server"], fs)
