import pytest
import os
import shutil
import filecmp
import time
import platform
import difflib
import sys
from freezegun import freeze_time
from click.testing import CliRunner
from pyfakefs.fake_filesystem_unittest import Pause
from typing import List
from src import verify

scenario_output_path = '../Scenarios/Output'
fake_ref_root_path = '/ref'


@pytest.fixture(scope="session", autouse=True)
def set_timezone():
    """Fakes the host timezone to UTC so we don't get different mhl files if the tests run on different time zones
    seems like freezegun can't handle timezones like we want"""
    os.environ['TZ'] = 'UTZ'
    time.tzset()


@pytest.fixture(autouse=True)
def set_hostname(monkeypatch):
    def fake_hostname():
        return 'myHost.local'
    monkeypatch.setattr(platform, 'node', fake_hostname)


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


def compare_file_content(reference, path, fake_fs=None, overwrite_ref=False):
    if os.path.isabs(path):
        relative_path = path.lstrip(os.sep)
    else:
        relative_path = path
    ref_path = os.path.join(fake_ref_root_path, reference, relative_path)

    if os.path.isfile(path) is True and os.path.isfile(ref_path) is True:
        result = filecmp.cmp(ref_path, path, shallow=False)
        if result is not True:
            print('\ngot different files:\n')
            for line in calculate_diff_of_files(ref_path, path):
                print(line.rstrip())
    else:
        result = False

    return result


def calculate_diff_of_files(path_a: str, path_b: str):
    with open(path_a, 'r') as file:
        data_a = file.readlines()
    with open(path_b, 'r') as file:
        data_b = file.readlines()
    return difflib.unified_diff(data_a, data_b, fromfile=path_a, tofile=path_b, n=2, lineterm='')


def replace_reference_files_if_needed(scenario_reference: str, folder_paths: List[str], fake_fs) -> None:
    """
    checks if the scenario reference folder exists in the output folder if it doesn't we copy the folders there and
    consider it as reference. This way we can easily recreate the reference files of a scenario by deleting it on disk
    and running the tests
    """
    real_ref_path = os.path.join(scenario_output_path, scenario_reference)
    with Pause(fake_fs):
        if os.path.isdir(real_ref_path):
            return

    for folder_path in folder_paths:
        assert os.path.isabs(folder_path)
        copy_fake_directory_to_real_fs(folder_path, real_ref_path, fake_fs)

    # reload the fake fs so it reflects the updated reference
    shutil.rmtree(fake_ref_root_path)
    load_real_reference(fake_fs)


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

    """

    # assume the card is copied to a travel drive.
    shutil.copytree('/A002R2EC', '/travel_01/A002R2EC')

    # create original mhl generation
    runner = CliRunner()
    result = runner.invoke(verify, ['/travel_01/A002R2EC'])
    assert result.exit_code == 0
    replace_reference_files_if_needed('scenario_01', ['/travel_01/A002R2EC'], fs)
    assert compare_file_content('scenario_01', '/travel_01/A002R2EC/asc-mhl/A002R2EC_2020-01-16_091500_0001.ascmhl')


@freeze_time("2020-01-16 09:15:00")
def test_scenario_02(fs, reference, A002R2EC):
    """

    """

    # assume the card is copied to a travel drive.
    shutil.copytree('/A002R2EC', '/travel_01/A002R2EC')

    # create original mhl generation of first copy
    runner = CliRunner()
    result = runner.invoke(verify, ['/travel_01/A002R2EC'])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        # assume the card is copied from the travel drive to a file server
        shutil.copytree('/travel_01/A002R2EC', '/file_server/A002R2EC')

        # create second mhl generation by verifying hashes on the file server
        result = runner.invoke(verify, ['/file_server/A002R2EC'])
        assert result.exit_code == 0
        replace_reference_files_if_needed('scenario_02', ['/travel_01', '/file_server'], fs)

        # verify there is only first generation on the travel drive, no second generation
        assert compare_file_content('scenario_02',
                                    '/travel_01/A002R2EC/asc-mhl/A002R2EC_2020-01-16_091500_0001.ascmhl')
        assert not os.path.isfile('/travel_01/A002R2EC/asc-mhl/A002R2EC_2020-01-17_143000_0002.ascmhl')

        # but a second generation on the file server
        assert compare_file_content('scenario_02',
                                    '/file_server/A002R2EC/asc-mhl/A002R2EC_2020-01-16_091500_0001.ascmhl')
        assert compare_file_content('scenario_02',
                                    '/file_server/A002R2EC/asc-mhl/A002R2EC_2020-01-17_143000_0002.ascmhl')


@freeze_time("2020-01-16 09:15:00")
def test_scenario_05(fs, reference, A002R2EC, A003R2EC):
    """

    """

    os.makedirs('/travel_01/Reels')
    os.makedirs('/file_server')

    # the card A002R2EC is copied in the Reels folder on a travel drive.
    shutil.copytree('/A002R2EC', '/travel_01/Reels/A002R2EC')
    # create first mhl generation of A002R2EC
    runner = CliRunner()
    result = runner.invoke(verify, ['/travel_01/Reels/A002R2EC'])
    assert result.exit_code == 0

    # the card A003R2EC is copied in the same Reels folder on the same travel drive.
    shutil.copytree('/A003R2EC', '/travel_01/Reels/A003R2EC')

    # create first mhl generation of A003R2EC
    runner = CliRunner()
    result = runner.invoke(verify, ['/travel_01/Reels/A003R2EC'])
    assert result.exit_code == 0

    with freeze_time("2020-01-17 14:30:00"):
        # the common Reels folder is copied to a file server.
        shutil.copytree('/travel_01/Reels', '/file_server/Reels')

        # An arbitrary file `Summary.txt` is added to the `Reels` folder.
        fs.create_file('/file_server/Reels/Summary.txt',
                       contents='This is a random summary\n\n* A002R2EC\n* A003R2EC\n')

        # The `Reels` folder is verified on the file server.
        runner = CliRunner()
        result = runner.invoke(verify, ['/file_server/Reels'])
        assert result.exit_code == 0
        replace_reference_files_if_needed('scenario_05', ['/travel_01', '/file_server'], fs)

        # check generations on the travel drive, they only exist inside the individual cards
        assert compare_file_content('scenario_05',
                                    '/travel_01/Reels/A002R2EC/asc-mhl/A002R2EC_2020-01-16_091500_0001.ascmhl')
        assert compare_file_content('scenario_05',
                                    '/travel_01/Reels/A003R2EC/asc-mhl/A003R2EC_2020-01-16_091500_0001.ascmhl')

        # check generations on the file server, a second generation exists for each card
        # and a initial one for the Reels folder that references the child histories
        assert compare_file_content('scenario_05',
                                    '/file_server/Reels/A002R2EC/asc-mhl/A002R2EC_2020-01-17_143000_0002.ascmhl')
        assert compare_file_content('scenario_05',
                                    '/file_server/Reels/A003R2EC/asc-mhl/A003R2EC_2020-01-17_143000_0002.ascmhl')
        assert compare_file_content('scenario_05',
                                    '/file_server/Reels/asc-mhl/Reels_2020-01-17_143000_0001.ascmhl')
