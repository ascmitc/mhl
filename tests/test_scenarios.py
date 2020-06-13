"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import pytest
import os
import shutil
import filecmp
import difflib
from freezegun import freeze_time
from click.testing import CliRunner
from pyfakefs.fake_filesystem_unittest import Pause
from typing import List

import mhl.commands

scenario_output_path = 'examples/scenarios/Output'
fake_ref_root_path = '/ref'


@pytest.fixture()
def reference(fs):
    load_real_reference(fs)


@pytest.fixture
@freeze_time("2020-01-15 13:00:00")
def A002R2EC(fs):
    fs.create_file('/A002R2EC/Sidecar.txt', contents='BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n')
    fs.create_file('/A002R2EC/Clips/A002C006_141024_R2EC.mov', contents='abcd\n')
    fs.create_file('/A002R2EC/Clips/A002C007_141024_R2EC.mov', contents='def\n')


@pytest.fixture
@freeze_time("2020-01-15 13:30:00")
def A003R2EC(fs):
    fs.create_file('/A003R2EC/Sidecar.txt', contents='Dolor sit amet, consetetur sadipscing elitr.\n')
    fs.create_file('/A003R2EC/Clips/A003C011_141024_R2EC.mov', contents='vbgh\n')
    fs.create_file('/A003R2EC/Clips/A003C012_141024_R2EC.mov', contents='zhgdr\n')


def load_real_reference(fake_fs):
    fake_fs.add_real_directory(scenario_output_path, target_path=fake_ref_root_path)


# custom dircmp to compare file contents as suggested in https://stackoverflow.com/a/24860799
class content_dircmp(filecmp.dircmp):
    """
    Compare the content of dir1 and dir2. In contrast with filecmp.dircmp, this
    subclass compares the content of files with the same path.
    """
    def phase3(self):
        """
        Find out differences between common files.
        Ensure we are using content comparison with shallow=False.
        """
        fcomp = filecmp.cmpfiles(self.left, self.right, self.common_files,
                                 shallow=False)
        self.same_files, self.diff_files, self.funny_files = fcomp


def dirs_are_equal(dir1, dir2):
    """
    Compare two directory trees content.
    Return False if they differ, True is they are the same.
    """
    result = True
    compared = content_dircmp(dir1, dir2, ignore=['.DS_Store'])
    if compared.left_only or compared.right_only or compared.diff_files or compared.funny_files:
        compared.report_partial_closure()
        for file in compared.diff_files:
            print_diff_of_files(os.path.join(dir1, file), os.path.join(dir2, file))
        result = False
    for subdir in compared.common_dirs:
        if not dirs_are_equal(os.path.join(dir1, subdir), os.path.join(dir2, subdir)):
            result = False
    return result


def compare_dir_content(reference, dir_path):
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


def print_diff_of_files(path_a: str, path_b: str):
    with open(path_a, 'r') as file:
        data_a = file.readlines()
    with open(path_b, 'r') as file:
        data_b = file.readlines()
    diff = difflib.unified_diff(data_a, data_b, fromfile=path_a, tofile=path_b, n=2, lineterm='')
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
        assert os.path.isabs(folder_path)
        if compare_mode:
            result &= compare_dir_content(scenario_reference, folder_path)
        else:
            copy_fake_directory_to_real_fs(folder_path, real_ref_path, fake_fs)

    return result


def copy_fake_directory_to_real_fs(fake_dir: str, real_dir: str, fake_fs):
    """ Utility function to copy a directory in the fake file system recursively to the real file system """
    for root, _, file_names in os.walk(fake_dir):
        relative_root = root.lstrip(os.sep)
        current_real_dir = os.path.join(real_dir, relative_root)
        with Pause(fake_fs):
            os.makedirs(current_real_dir)
        for file_name in file_names:
            with open(os.path.join(root, file_name), 'rb') as file:
                data = file.read()
            with Pause(fake_fs):
                with open(os.path.join(current_real_dir, file_name), 'w+b') as dst_file:
                    dst_file.write(data)


@freeze_time("2020-01-16 09:15:00")
def test_scenario_01(fs, reference, A002R2EC):
    """
    This is the most basic example. A camera card is copied to a travel drive and an ASC-MHL file is
    created with hashes of all files on the card.
    """

    # assume the card is copied to a travel drive.
    shutil.copytree('/A002R2EC', '/travel_01/A002R2EC')

    # create original mhl generation
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/travel_01/A002R2EC'])
    assert result.exit_code == 0
    assert compare_files_against_reference('scenario_01', ['/travel_01'], fs)


@freeze_time("2020-01-16 09:15:00")
def test_scenario_02(fs, reference, A002R2EC):
    """
    In this scenario a copy is made, and then a copy of the copy. Two ASC-MHL are created during
    this process, documenting the history of both copy processes.
    """

    # assume the card is copied to a travel drive.
    shutil.copytree('/A002R2EC', '/travel_01/A002R2EC')

    # create original mhl generation of first copy
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/travel_01/A002R2EC'])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        # assume the card is copied from the travel drive to a file server
        shutil.copytree('/travel_01/A002R2EC', '/file_server/A002R2EC')

        # create second mhl generation by verifying hashes on the file server
        result = runner.invoke(mhl.commands.seal, ['/file_server/A002R2EC'])
        assert result.exit_code == 0
        assert compare_files_against_reference('scenario_02', ['/travel_01', '/file_server'], fs)

        # verify there is only first generation on the travel drive, no second generation
        # but a second generation on the file server


@freeze_time("2020-01-16 09:15:00")
def test_scenario_03(fs, reference, A002R2EC):
    """
    In this scenario the first hashes are created using the xxhash format. Different hash formats
    might be required by systems used further down the workflow, so the second copy is verified
    against the existing xxhash hashes, and additional MD5 hashes can be created and stored during
    that process on demand.
    """

    # assume the card is copied to a travel drive.
    shutil.copytree('/A002R2EC', '/travel_01/A002R2EC')

    # create original mhl generation of first copy
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/travel_01/A002R2EC'])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        # assume the card is copied from the travel drive to a file server
        shutil.copytree('/travel_01/A002R2EC', '/file_server/A002R2EC')

        # The files are verified on the file server, and additional ("secondary") MD5 hashes are created.
        result = runner.invoke(mhl.commands.seal, ['-h', 'MD5', '/file_server/A002R2EC'])
        assert result.exit_code == 0
        assert compare_files_against_reference('scenario_03', ['/travel_01', '/file_server'], fs)

        # the second generation will include both the generated secondary hashes and the original hash verified


@freeze_time("2020-01-16 09:15:00")
def test_scenario_04(fs, reference, A002R2EC):
    """
    Copying a folder to a travel drive and from there to a file server with a hash mismatch in
    one file.
    """

    # assume the card is copied to a travel drive.
    shutil.copytree('/A002R2EC', '/travel_01/A002R2EC')

    # create original mhl generation of first copy
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/travel_01/A002R2EC'])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        # assume the card is copied from the travel drive to a file server
        shutil.copytree('/travel_01/A002R2EC', '/file_server/A002R2EC')

        # simulate that during the copy the `Sidecar.txt` got corrupt (altered)
        with open('/file_server/A002R2EC/Sidecar.txt', "a") as file:
            file.write('!!')

        # The files are verified on the file server, the altered file will cause the verification to fail.
        result = runner.invoke(mhl.commands.seal, ['/file_server/A002R2EC'])
        assert result.exit_code == 12
        assert compare_files_against_reference('scenario_04', ['/travel_01', '/file_server'], fs)

        # the second generation will include the failed verification result


@freeze_time("2020-01-16 09:15:00")
def test_scenario_05(fs, reference, A002R2EC, A003R2EC):
    """
    Copying two camera mags to a `Reels` folder on a travel drive, and the entire `Reels` folder
    folder to a server.
    """

    os.makedirs('/travel_01/Reels')
    os.makedirs('/file_server')

    # the card A002R2EC is copied in the Reels folder on a travel drive.
    shutil.copytree('/A002R2EC', '/travel_01/Reels/A002R2EC')
    # create first mhl generation of A002R2EC
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/travel_01/Reels/A002R2EC'])
    assert result.exit_code == 0

    # the card A003R2EC is copied in the same Reels folder on the same travel drive.
    shutil.copytree('/A003R2EC', '/travel_01/Reels/A003R2EC')

    # create first mhl generation of A003R2EC
    runner = CliRunner()
    result = runner.invoke(mhl.commands.seal, ['/travel_01/Reels/A003R2EC'])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        # the common Reels folder is copied to a file server.
        shutil.copytree('/travel_01/Reels', '/file_server/Reels')

        # An arbitrary file `Summary.txt` is added to the `Reels` folder.
        fs.create_file('/file_server/Reels/Summary.txt',
                       contents='This is a random summary\n\n* A002R2EC\n* A003R2EC\n')

        # The `Reels` folder is verified on the file server.
        runner = CliRunner()
        result = runner.invoke(mhl.commands.seal, ['/file_server/Reels'])
        assert result.exit_code == 0
        assert compare_files_against_reference('scenario_05', ['/travel_01', '/file_server'], fs)

        # check generations on the travel drive, they only exist inside the individual cards
        # check generations on the file server, a second generation exists for each card
        # and a initial one for the Reels folder that references the child histories
